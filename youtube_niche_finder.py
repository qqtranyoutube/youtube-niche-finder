import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import requests

st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")

# Lấy API Key từ secrets.toml
api_key = st.secrets["YOUTUBE_API_KEY"]

st.title("🎯 YouTube Keyword Analyzer PRO")
st.write("Phân tích từ khóa & video YouTube đang tăng trưởng mạnh mẽ 🚀")

keyword = st.text_input("🔍 Nhập từ khóa chủ đề YouTube:", value="ai")

def get_keyword_suggestions(query):
    try:
        response = requests.get(
            f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={query}"
        )
        suggestions = response.json()[1]
        return suggestions
    except Exception as e:
        st.error(f"Lỗi khi lấy gợi ý từ khóa: {e}")
        return []

def get_video_results(query, api_key):
    youtube = build("youtube", "v3", developerKey=api_key)
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=10,
        order="viewCount"
    )
    response = request.execute()
    videos = []
    for item in response.get("items", []):
        video_data = {
            "Tiêu đề": item["snippet"]["title"],
            "Kênh": item["snippet"]["channelTitle"],
            "Ngày đăng": item["snippet"]["publishedAt"][:10],
            "Video ID": item["id"]["videoId"],
            "Link": f"https://www.youtube.com/watc
