import json
from datetime import datetime, timezone

import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="YT Comment Miner",
    page_icon="🎬",
    layout="centered",
)

# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Background */
.stApp {
    background: #0a0a0f;
    color: #f0f0f8;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 3rem; padding-bottom: 4rem; max-width: 640px; }

/* Title */
.yt-title {
    font-size: 3rem;
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -0.025em;
    margin-bottom: 0.5rem;
}
.yt-title em { color: #ff2d55; font-style: normal; }

.yt-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    color: #f2f2f5;
    line-height: 1.7;
    margin-bottom: 2.5rem;
}

/* Input overrides */
div[data-testid="stTextInput"] input {
    background: #16161f !important;
    border: 1px solid #2a2a3a !important;
    border-radius: 11px !important;
    color: #f5f5f5 !important;
    font-family: 'DM Mono', monospace !important;
    padding: 0.8rem 1rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #ff2d55 !important;
    box-shadow: 0 0 0 3px rgba(255,45,85,0.12) !important;
}

/* Slider */
div[data-testid="stSlider"] > div > div > div {
    background: #ff2d55 !important;
}

/* Button */
div[data-testid="stButton"] > button {
    background: #ff2d55 !important;
    color: white !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 1.5rem !important;
    width: 100% !important;
    box-shadow: 0 4px 24px rgba(255,45,85,0.4) !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 36px rgba(255,45,85,0.5) !important;
}

/* Download button */
div[data-testid="stDownloadButton"] > button {
    background: #4CAF72 !important;
    color: #0a0a0f !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    width: 100% !important;
    padding: 0.75rem 1.5rem !important;
    box-shadow: 0 4px 20px rgba(76,175,114,0.35) !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* Status boxes */
div[data-testid="stInfo"],
div[data-testid="stSuccess"],
div[data-testid="stError"],
div[data-testid="stWarning"] {
    border-radius: 12px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: #16161f;
    border: 1px solid #2a2a3a;
    border-radius: 14px;
    padding: 1rem 1.2rem;
}
div[data-testid="metric-container"] label {
    color: #f5f5f5 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #f0f0f8 !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}

/* Progress */
div[data-testid="stProgress"] > div > div {
    background: #ff2d55 !important;
}

/* Divider */
hr { border-color: #2a2a3a !important; margin: 1.5rem 0 !important; }

/* Log expander */
details {
    background: #16161f !important;
    border: 1px solid #2a2a3a !important;
    border-radius: 12px !important;
    padding: 0.5rem 1rem !important;
}
details summary {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #6b6b88 !important;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="yt-title">Mine <em>every</em><br>comment.</div>
<div class="yt-sub">
  Введи запит → натисни кнопку → завантаж JSON.<br>
</div>
""", unsafe_allow_html=True)

# ── API key from secrets ───────────────────────────────────────────────────────

try:
    API_KEY = st.secrets["API_KEY_YOUTUBE"]
except KeyError:
    st.error("⚠ API_KEY_YOUTUBE не знайдено в Streamlit Secrets. Додай його в Settings → Secrets.")
    st.stop()

# ── YouTube helpers ───────────────────────────────────────────────────────────

def get_client():
    return build("youtube", "v3", developerKey=API_KEY)


def search_videos(youtube, query: str, max_videos: int):
    videos, next_page_token = [], None
    while len(videos) < max_videos:
        batch = min(50, max_videos - len(videos))
        resp = youtube.search().list(
            q=query, type="video", part="id,snippet",
            maxResults=batch, pageToken=next_page_token,
        ).execute()
        for item in resp.get("items", []):
            videos.append({
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "published_at": item["snippet"]["publishedAt"],
                "description": item["snippet"]["description"],
            })
        next_page_token = resp.get("nextPageToken")
        if not next_page_token:
            break
    return videos


def get_replies(youtube, comment_id: str):
    replies, next_page_token = [], None
    while True:
        resp = youtube.comments().list(
            parentId=comment_id, part="snippet",
            maxResults=100, pageToken=next_page_token,
        ).execute()
        for item in resp.get("items", []):
            s = item["snippet"]
            replies.append({
                "id": item["id"],
                "author": s["authorDisplayName"],
                "text": s["textDisplay"],
                "likes": s["likeCount"],
                "published_at": s["publishedAt"],
                "updated_at": s["updatedAt"],
            })
        next_page_token = resp.get("nextPageToken")
        if not next_page_token:
            break
    return replies


def get_comments(youtube, video_id: str):
    comments, next_page_token = [], None
    while True:
        resp = youtube.commentThreads().list(
            videoId=video_id, part="snippet",
            maxResults=100, pageToken=next_page_token,
        ).execute()
        for item in resp.get("items", []):
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
        next_page_token = resp.get("nextPageToken")
        if not next_page_token:
            break
    return comments

# ── UI ────────────────────────────────────────────────────────────────────────

query = st.text_input(
    "Search Query",
    placeholder="наприклад: AI stylist app review",
    label_visibility="visible",
)

max_videos = st.slider("Max Videos", min_value=1, max_value=100, value=10)

run = st.button("🔍  Scrape Comments")

# ── Scrape ────────────────────────────────────────────────────────────────────

if run:
    if not query.strip():
        st.warning("Введи пошуковий запит.")
        st.stop()

    youtube = get_client()
    log_lines = []

    st.divider()

    with st.status("Scraping YouTube…", expanded=True) as status:

        # Search
        st.write(f"🔎 Searching for **{query}**…")
        try:
            videos = search_videos(youtube, query, max_videos)
        except HttpError as e:
            st.error(f"YouTube API error: {e}")
            st.stop()

        st.write(f"Found **{len(videos)}** videos. Fetching comments…")

        results = []
        total_comments = 0
        progress = st.progress(0)

        for i, video in enumerate(videos):
            progress.progress((i + 1) / len(videos))
            try:
                comments = get_comments(youtube, video["video_id"])
                total_comments += len(comments)
                results.append({**video, "comment_count": len(comments), "comments": comments})
                log_lines.append(f"✓ [{i+1}/{len(videos)}] {video['title'][:60]} — {len(comments)} comments")
                st.write(f"✓ `{video['title'][:55]}` — **{len(comments)}** comments")
            except HttpError as e:
                reason = e.error_details[0]["reason"] if e.error_details else str(e)
                if reason == "commentsDisabled":
                    results.append({**video, "comment_count": 0, "comments": [], "note": "comments disabled"})
                    log_lines.append(f"— [{i+1}] {video['title'][:60]} — comments disabled")
                elif reason == "quotaExceeded":
                    st.warning("⚠ YouTube API quota exceeded. Saving partial results.")
                    break
                else:
                    results.append({**video, "comment_count": 0, "comments": [], "note": reason})
                    log_lines.append(f"✗ [{i+1}] {video['title'][:60]} — {reason}")

        progress.progress(1.0)
        status.update(label="Done!", state="complete", expanded=False)

    # ── Results ───────────────────────────────────────────────────────────────

    now = datetime.now(timezone.utc)
    output = {
        "query": query,
        "scraped_at": now.isoformat(),
        "video_count": len(results),
        "total_comments": total_comments,
        "videos": results,
    }

    safe_query = query.replace(" ", "_")[:40]
    filename = f"{safe_query}_{now.strftime('%Y%m%d_%H%M%S')}.json"
    json_bytes = json.dumps(output, indent=2, ensure_ascii=False).encode("utf-8")

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Videos", len(results))
    col2.metric("Comments", total_comments)
    col3.metric("File size", f"{len(json_bytes) / 1024:.0f} KB")

    st.download_button(
        label="⬇  Download JSON",
        data=json_bytes,
        file_name=filename,
        mime="application/json",
    )
