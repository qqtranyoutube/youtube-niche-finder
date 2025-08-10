import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")
st.title("📊 YouTube Keyword Analyzer PRO")

# --- Đọc key từ secrets hoặc input ---
if "YOUTUBE_API_KEY" in st.secrets:
    api_key = st.secrets["YOUTUBE_API_KEY"]
else:
    api_key = st.text_input("🔑 Nhập YouTube API Key", type="password")

if api_key:
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        
        # Test gọi API
        request = youtube.videos().list(
            part="snippet",
            chart="mostPopular",
            maxResults=1,
            regionCode="US"
        )
        response = request.execute()
        
        st.success("✅ API key hợp lệ!")
        st.json(response)

    except HttpError as e:
        st.error(f"❌ YouTube API Error: {e}")
else:
    st.warning("⚠️ Vui lòng nhập API key để tiếp tục.")
