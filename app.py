import json
from datetime import datetime, timezone

import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="YT Comment Miner",
    page_icon="🛸",
    layout="centered",
)

# ── Styling ───────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

/* ── Deep space background ── */
.stApp {
    background: #06060f;
    color: #dcdcff;
}

/* Nebula layer */
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background:
        radial-gradient(ellipse 55% 45% at 15% 55%, rgba(99,60,180,0.09) 0%, transparent 65%),
        radial-gradient(ellipse 45% 55% at 85% 25%, rgba(56,120,240,0.07) 0%, transparent 65%),
        radial-gradient(ellipse 35% 45% at 55% 85%, rgba(130,80,220,0.06) 0%, transparent 65%),
        radial-gradient(ellipse 60% 30% at 50% 5%,  rgba(80,80,200,0.05) 0%, transparent 70%);
    pointer-events: none; z-index: 0;
}

/* Star field */
.stApp::after {
    content: '';
    position: fixed; inset: 0;
    background-image:
        radial-gradient(1px 1px at  8% 12%, rgba(200,200,255,0.55) 0%, transparent 100%),
        radial-gradient(1px 1px at 22% 38%, rgba(200,200,255,0.35) 0%, transparent 100%),
        radial-gradient(1.5px 1.5px at 38%  7%, rgba(220,220,255,0.65) 0%, transparent 100%),
        radial-gradient(1px 1px at 53% 58%, rgba(200,200,255,0.28) 0%, transparent 100%),
        radial-gradient(1px 1px at 67% 22%, rgba(200,200,255,0.45) 0%, transparent 100%),
        radial-gradient(1.5px 1.5px at 78% 68%, rgba(220,220,255,0.55) 0%, transparent 100%),
        radial-gradient(1px 1px at 88% 42%, rgba(200,200,255,0.38) 0%, transparent 100%),
        radial-gradient(1px 1px at 14% 77%, rgba(200,200,255,0.30) 0%, transparent 100%),
        radial-gradient(1px 1px at 58% 88%, rgba(200,200,255,0.45) 0%, transparent 100%),
        radial-gradient(1px 1px at 32% 62%, rgba(200,200,255,0.35) 0%, transparent 100%),
        radial-gradient(1px 1px at 45% 32%, rgba(200,200,255,0.28) 0%, transparent 100%),
        radial-gradient(1.5px 1.5px at 92% 18%, rgba(220,220,255,0.50) 0%, transparent 100%),
        radial-gradient(1px 1px at 72%  5%, rgba(200,200,255,0.40) 0%, transparent 100%),
        radial-gradient(1px 1px at  3% 50%, rgba(200,200,255,0.32) 0%, transparent 100%),
        radial-gradient(1px 1px at 95% 80%, rgba(200,200,255,0.38) 0%, transparent 100%);
    pointer-events: none; z-index: 0;
}

/* ── Layout ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 4.5rem;
    padding-bottom: 5rem;
    max-width: 560px;
    position: relative;
    z-index: 1;
}

/* ── Header ── */
.yt-eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: #7c6ff7;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.yt-eyebrow::before, .yt-eyebrow::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(124,111,247,0.4));
}
.yt-eyebrow::after {
    background: linear-gradient(90deg, rgba(124,111,247,0.4), transparent);
}

.yt-title {
    font-size: 3rem;
    font-weight: 700;
    line-height: 1.08;
    letter-spacing: -0.03em;
    margin-bottom: 1rem;
    color: #dcdcff;
}
.yt-title em {
    font-style: normal;
    background: linear-gradient(125deg, #a78bfa 0%, #818cf8 40%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.yt-sub {
    font-family: 'Space Mono', monospace;
    font-size: 0.73rem;
    color: #3a3a5c;
    line-height: 1.85;
    margin-bottom: 2.8rem;
}

/* ── Input ── */
div[data-testid="stTextInput"] label {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: #3a3a5c !important;
}
div[data-testid="stTextInput"] input {
    background: rgba(124,111,247,0.04) !important;
    border: 1px solid rgba(124,111,247,0.18) !important;
    border-radius: 12px !important;
    color: #dcdcff !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.88rem !important;
    padding: 0.85rem 1.1rem !important;
    transition: all 0.25s ease !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #252545 !important; }
div[data-testid="stTextInput"] input:focus {
    border-color: rgba(124,111,247,0.55) !important;
    background: rgba(124,111,247,0.07) !important;
    box-shadow: 0 0 0 3px rgba(124,111,247,0.1), 0 0 24px rgba(124,111,247,0.12) !important;
}

/* ── Slider ── */
div[data-testid="stSlider"] label {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: #3a3a5c !important;
}
div[data-testid="stSlider"] > div > div > div {
    background: linear-gradient(90deg, #7c6ff7, #818cf8, #60a5fa) !important;
}
div[data-testid="stSlider"] > div > div > div > div {
    background: #dcdcff !important;
    border: 2px solid #7c6ff7 !important;
    box-shadow: 0 0 14px rgba(124,111,247,0.6), 0 0 28px rgba(124,111,247,0.2) !important;
    width: 18px !important; height: 18px !important;
}

/* ── Main button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #6d5ce7 0%, #7c6ff7 40%, #60a5fa 100%) !important;
    color: white !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.03em !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.82rem 2rem !important;
    width: 100% !important;
    box-shadow: 0 4px 28px rgba(109,92,231,0.4), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stButton"] > button:hover {
    box-shadow: 0 8px 44px rgba(109,92,231,0.55), inset 0 1px 0 rgba(255,255,255,0.2) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stButton"] > button:active { transform: translateY(0) !important; }

/* ── Download button ── */
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #10b981 0%, #34d399 100%) !important;
    color: #06060f !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border: none !important;
    border-radius: 12px !important;
    width: 100% !important;
    padding: 0.82rem 2rem !important;
    box-shadow: 0 4px 24px rgba(16,185,129,0.3), inset 0 1px 0 rgba(255,255,255,0.2) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    box-shadow: 0 8px 36px rgba(16,185,129,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Alert boxes ── */
div[data-testid="stInfo"],
div[data-testid="stSuccess"],
div[data-testid="stError"],
div[data-testid="stWarning"] {
    border-radius: 12px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
}

/* ── st.status ── */
div[data-testid="stStatusWidget"] {
    background: rgba(124,111,247,0.04) !important;
    border: 1px solid rgba(124,111,247,0.18) !important;
    border-radius: 14px !important;
}
div[data-testid="stStatusWidget"] p,
div[data-testid="stStatusWidget"] span {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.76rem !important;
    color: #4a4a7a !important;
}

/* ── Metrics ── */
div[data-testid="metric-container"] {
    background: rgba(124,111,247,0.04);
    border: 1px solid rgba(124,111,247,0.14);
    border-radius: 16px;
    padding: 1.1rem 1.2rem;
}
div[data-testid="metric-container"] label {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: #3a3a5c !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #dcdcff !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* ── Progress ── */
div[data-testid="stProgress"] > div {
    background: rgba(255,255,255,0.05) !important;
    border-radius: 4px !important;
    overflow: hidden !important;
}
div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #7c6ff7, #818cf8, #60a5fa) !important;
    border-radius: 4px !important;
    box-shadow: 0 0 12px rgba(124,111,247,0.6) !important;
}

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid rgba(124,111,247,0.1) !important;
    margin: 2rem 0 !important;
}

/* ── Expander ── */
div[data-testid="stExpander"] {
    background: rgba(124,111,247,0.03) !important;
    border: 1px solid rgba(124,111,247,0.14) !important;
    border-radius: 12px !important;
}
div[data-testid="stExpander"] summary {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.72rem !important;
    color: #3a3a5c !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(124,111,247,0.25); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="yt-eyebrow">YT Comment Miner</div>
<div class="yt-title">Mine <em>every</em><br>comment.</div>
<div class="yt-sub">
  Введи запит → натисни кнопку → завантаж JSON<br>
  API ключ зберігається в Streamlit Secrets — у браузер не потрапляє
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

run = st.button("✦  Scrape Comments")

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
