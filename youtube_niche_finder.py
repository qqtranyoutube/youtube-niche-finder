import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --------------------- PAGE CONFIG ---------------------
st.set_page_config(page_title="YouTube Analyzer", layout="wide")
st.title("📊 YouTube Analyzer — Stable Version")

# --------------------- API KEY CONFIG ---------------------
# Lấy API key từ secrets
api_key = st.secrets.get("YOUTUBE_API_KEY", None)

# Hướng dẫn nếu chưa cấu hình API key
if not api_key:
    st.error("🚨 **YouTube API Key chưa được cấu hình** trong `.streamlit/secrets.toml`.")
    st.markdown("""
    **Cách khắc phục**:
    1. Mở file `.streamlit/secrets.toml`
    2. Thêm dòng:
       ```
       YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"
       ```
    3. Lưu lại và chạy lại ứng dụng.
    """)
    st.stop()

# --------------------- YOUTUBE API CLIENT ---------------------
def get_youtube_client(api_key):
    try:
        return build("youtube", "v3", developerKey=api_key)
    except Exception as e:
        st.error(f"❌ Lỗi khi khởi tạo YouTube API: `{e}`")
        st.stop()

youtube = get_youtube_client(api_key)

# --------------------- SEARCH FUNCTION ---------------------
def search_videos(query, max_results=5):
    try:
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            order="date"
        )
        response = request.execute()
        return response
    except HttpError as e:
        if e.resp.status == 400:
            st.error("🚨 **API Key không hợp lệ hoặc đã hết hạn!**")
            st.markdown("""
            **Cách khắc phục**:
            1. Kiểm tra lại API key trong `.streamlit/secrets.toml`
            2. Đảm bảo API key này đã bật **YouTube Data API v3** trong Google Cloud Console
            3. Nếu key đã đúng, hãy tạo một key mới.
            """)
        else:
            st.error(f"❌ Lỗi YouTube API: {e}")
        st.stop()

# --------------------- MAIN APP ---------------------
query = st.text_input("🔍 Nhập từ khóa tìm kiếm video", "meditation music")
max_results = st.slider("Số lượng video", 1, 20, 5)

if st.button("Tìm kiếm"):
    data = search_videos(query, max_results)
    if data and "items" in data:
        df = pd.DataFrame([
            {
                "Video Title": item["snippet"]["title"],
                "Channel": item["snippet"]["channelTitle"],
                "Published At": item["snippet"]["publishedAt"],
                "Video URL": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }
            for item in data["items"]
        ])
        st.dataframe(df)
