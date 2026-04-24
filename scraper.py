import json
import os
import sys
from datetime import datetime, timezone

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_youtube_client():
    api_key = os.environ.get("API_KEY_YOUTUBE", "")
    if not api_key:
        print("ERROR: API_KEY_YOUTUBE environment variable is not set.")
        sys.exit(1)
    return build("youtube", "v3", developerKey=api_key)


def search_videos(youtube, query, max_videos=100):
    videos = []
    next_page_token = None

    while len(videos) < max_videos:
        batch_size = min(50, max_videos - len(videos))
        response = youtube.search().list(
            q=query,
            type="video",
            part="id,snippet",
            maxResults=batch_size,
            pageToken=next_page_token,
        ).execute()

        for item in response.get("items", []):
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "published_at": item["snippet"]["publishedAt"],
                "description": item["snippet"]["description"],
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return videos


def get_replies(youtube, comment_id):
    replies = []
    next_page_token = None

    while True:
        response = youtube.comments().list(
            parentId=comment_id,
            part="snippet",
            maxResults=100,
            pageToken=next_page_token,
        ).execute()

        for item in response.get("items", []):
            s = item["snippet"]
            replies.append({
                "id": item["id"],
                "author": s["authorDisplayName"],
                "text": s["textDisplay"],
                "likes": s["likeCount"],
                "published_at": s["publishedAt"],
                "updated_at": s["updatedAt"],
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return replies


def get_comments(youtube, video_id):
    comments = []
    next_page_token = None

    while True:
        response = youtube.commentThreads().list(
            videoId=video_id,
            part="snippet",
            maxResults=100,
            pageToken=next_page_token,
        ).execute()

        for item in response.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            comment = {
                "id": item["id"],
                "author": top["authorDisplayName"],
                "text": top["textDisplay"],
                "likes": top["likeCount"],
                "published_at": top["publishedAt"],
                "updated_at": top["updatedAt"],
                "reply_count": item["snippet"]["totalReplyCount"],
                "replies": [],
            }
            if item["snippet"]["totalReplyCount"] > 0:
                comment["replies"] = get_replies(youtube, item["id"])
            comments.append(comment)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return comments


def scrape(query, max_videos=100):
    youtube = get_youtube_client()

    print(f"Searching for videos: '{query}'...")
    videos = search_videos(youtube, query, max_videos)
    print(f"Found {len(videos)} videos.\n")

    results = []
    total_comments = 0

    for i, video in enumerate(videos):
        print(f"[{i + 1}/{len(videos)}] {video['title'][:70]}")
        try:
            comments = get_comments(youtube, video["video_id"])
            print(f"    -> {len(comments)} comments fetched")
            total_comments += len(comments)
            results.append({**video, "comment_count": len(comments), "comments": comments})
        except HttpError as e:
            reason = e.error_details[0]["reason"] if e.error_details else str(e)
            if reason == "commentsDisabled":
                print(f"    -> Comments disabled, skipping")
                results.append({**video, "comment_count": 0, "comments": [], "note": "comments disabled"})
            elif reason == "quotaExceeded":
                print(f"\nQuota exceeded after {i} videos. Saving partial results...")
                break
            else:
                print(f"    -> Error: {reason}, skipping")
                results.append({**video, "comment_count": 0, "comments": [], "note": reason})

    now = datetime.now(timezone.utc)
    safe_query = query.replace(" ", "_")[:40]
    filename = f"{safe_query}_{now.strftime('%Y%m%d_%H%M%S')}.json"

    output = {
        "query": query,
        "scraped_at": now.isoformat(),
        "video_count": len(results),
        "total_comments": total_comments,
        "videos": results,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDone! {total_comments} comments from {len(results)} videos -> {filename}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <query> [max_videos]")
        sys.exit(1)

    query = sys.argv[1]
    max_videos = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    scrape(query, max_videos)
