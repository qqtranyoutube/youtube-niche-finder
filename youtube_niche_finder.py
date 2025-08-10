import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from io import BytesIO
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytrends.request import TrendReq
import os
import json

# ---------------- CONFIG ----------------
st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")
st.title("🚀 YouTube Keyword Analyzer PRO")
st.write("Phân tích từ khóa & video YouTube đang tăng trưởng mạnh mẽ")

# ---------------- API KEY CHECK ----------------
api_key = st.secrets.get("YOUTUBE_API_KEY") or os.getenv("YOUTUBE_API_KEY")
if not api_key:
    st.error("❌ Không tìm thấy YOUTUBE_API_KEY trong `.streamlit/secrets.toml` hoặc biến môi trường.")
    st.stop()

# Init YouTube API
try:
    youtube = build("youtube", "v3", developerKey=api_key)
except Exception as e:
    st.error(f"❌ Lỗi khởi tạo YouTube API: {str(e)}")
    st.stop()

# ---------------- INPUTS ----------------
topic = st.text_input("🧠 Nhập chủ đề (ví dụ: fitness, ai, sleep)", "")
region_code = st.text_input("🌎 Mã quốc gia (ISO 3166-1, ví dụ: US, VN, JP)", "US").upper()

use_trending = st.checkbox("📝 Tự động lấy từ khóa trending YouTube", value=True)
use_google_trends = st.checkbox("📈 Lấy từ khóa rising từ Google Trends", value=True)

# ---------------- FUNCTIONS ----------------
def get_suggestions(topic):
    """Lấy gợi ý từ khóa từ YouTube Suggest"""
    if not topic:
        return []
    try:
        suggestion_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={topic}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(suggestion_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()[1]
    except Exception as e:
        st.warning(f"⚠️ Lỗi lấy gợi ý từ khóa: {e}")
    return []

def get_trending_videos(region="US"):
    """Lấy video trending theo quốc gia"""
    try:
        request = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            maxResults=20,
            regionCode=region
        )
        response = request.execute()
    except HttpError as e:
        try:
            err_detail = json.loads(e.content.decode())
            st.error(f"❌ YouTube API Error {e.resp.status}: {err_detail['error']['message']}")
        except:
            st.error(f"❌ YouTube API Error: {str(e)}")
        return []
    except Exception as e:
        st.error(f"❌ Lỗi không xác định khi lấy trending: {str(e)}")
        return []

    videos = []
    for item in response.get("items", []):
        videos.append({
            "title": item["snippet"]["title"],
            "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
            "channel": item["snippet"]["channelTitle"],
            "views": int(item["statistics"].get("viewCount", 0))
        })
    return videos

def get_google_trends(keyword):
    """Lấy từ khóa rising từ Google Trends"""
    try:
        pytrend = TrendReq()
        pytrend.build_payload([keyword], cat=0, timeframe='now 7-d', geo='US', gprop='youtube')
        related = pytrend.related_queries()[keyword]['rising']
        if related is not None:
            return related['query'].tolist()
    except Exception as e:
        st.warning(f"⚠️ Lỗi lấy Google Trends: {e}")
    return []

# ---------------- DATA COLLECTION ----------------
all_keywords = []
trending_videos = []

if topic:
    all_keywords.extend(get_suggestions(topic))

if use_trending:
    trending_videos = get_trending_videos(region_code)
    all_keywords.extend([v["title"] for v in trending_videos])

if use_google_trends and topic:
    all_keywords.extend(get_google_trends(topic))

# ---------------- DEDUPLICATE ----------------
all_keywords = list(set(all_keywords))

st.markdown(f"""
🔑 **Tổng số từ khóa thu thập được: {len(all_keywords)}**
```python
{all_keywords}
