import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd

st.set_page_config(page_title="YouTube API Checker", layout="wide")
st.title("🔍 YouTube API Tool — Phiên bản ổn định")

# --- Lưu trạng thái API Key
if "api_key_valid" not in st.session_state:
    st.session_state.api_key_valid = False

# --- Nhập API Key
api_key = st.text_input("🔑 Nhập YouTube API Key:", type="password", value=st.secrets.get("YOUTUBE_API_KEY", ""))

# --- Hàm kiểm tra API Key
def check_api_key(key):
    try:
        youtube = build("youtube", "v3", developerKey=key)
        request = youtube.channels().list(part="snippet", id="UC_x5XG1OV2P6uZZ5FSM9Ttw")  # Channel Google Developers
        request.execute()
        return True
    except HttpError as e:
        if e.resp.status == 400:
            st.error("❌ API Key không hợp lệ hoặc đã bị thu hồi.")
            st.markdown("""
            **Hướng dẫn sửa:**
            1. Mở [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
            2. Tạo **API Key** mới.
            3. Kích hoạt **YouTube Data API v3**.
            4. Sao chép API Key vào ô nhập ở trên.
            """)
        else:
            st.error(f"🚨 Lỗi khác: {e}")
        return False

# --- Nút kiểm tra API Key
if st.button("✅ Kiểm tra API Key"):
    if api_key.strip() == "":
        st.warning("⚠️ Vui lòng nhập API Key trước khi kiểm tra.")
    else:
        st.session_state.api_key_valid = check_api_key(api_key)
        if st.session_state.api_key_valid:
            st.success("🎉 API Key hợp lệ! Bạn có thể bắt đầu tìm kiếm.")

# --- Chức năng tìm kiếm chỉ khi API Key hợp lệ
if st.session_state.api_key_valid:
    query = st.text_input("🔍 Nhập từ khóa tìm kiếm trên YouTube:")
    if st.button("Tìm kiếm video"):
        youtube = build("youtube", "v3", developerKey=api_key)
        search_response = youtube.search().list(
            q=query, part="snippet", maxResults=5
        ).execute()

        data = []
        for item in search_response["items"]:
            data.append({
                "Tiêu đề": item["snippet"]["title"],
                "Kênh": item["snippet"]["channelTitle"],
                "Ngày đăng": item["snippet"]["publishedAt"],
                "Link": f"https://www.youtube.com/watch?v={item['id'].get('videoId', '')}"
            })

        df = pd.DataFrame(data)
        st.dataframe(df)
else:
    st.info("💡 Hãy kiểm tra API Key trước khi chạy tìm kiếm.")
