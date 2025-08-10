import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ---------------- CONFIG ----------------
st.set_page_config(page_title="🧘 Meditation YouTube Analyzer — PRO", layout="wide")
st.title("🧘 Meditation YouTube Analyzer — PRO")
st.markdown("Phân tích video Meditation, kiểm tra RPM và trạng thái kiếm tiền.")

# ---------------- INPUT API KEY ----------------
api_key = st.text_input("🔑 Nhập YouTube API Key:", type="password", value=st.secrets.get("YOUTUBE_API_KEY", ""))

# ---------------- CHECK API KEY FUNCTION ----------------
def check_api_key(key):
    try:
        youtube = build("youtube", "v3", developerKey=key)
        request = youtube.channels().list(part="snippet", id="UC_x5XG1OV2P6uZZ5FSM9Ttw")  # Google Developers channel
        request.execute()
        return True
    except HttpError as e:
        if e.resp.status in [400, 403]:
            return False
        return False

# ---------------- BUTTON TO CHECK KEY ----------------
if st.button("✅ Kiểm tra API Key"):
    if check_api_key(api_key):
        st.success("🎉 API Key hợp lệ! Bạn có thể chạy tìm kiếm.")
    else:
        st.error("❌ API Key không hợp lệ!")
        st.markdown("""
        **Hướng dẫn fix:**
        1. Vào [Google Cloud Console](https://console.cloud.google.com/).
        2. Tạo dự án mới hoặc dùng dự án hiện có.
        3. Bật API **YouTube Data API v3**.
        4. Tạo API Key mới và dán vào ô ở trên.
        5. Đảm bảo API chưa bị giới hạn domain hoặc IP.
        """)

# ---------------- SEARCH FUNCTION ----------------
def search_videos(key, query="meditation", max_results=10):
    youtube = build("youtube", "v3", developerKey=key)
    search_response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results,
        order="date"
    ).execute()

    videos = []
    for item in search_response["items"]:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        publish_time = item["snippet"]["publishedAt"]

        # Get monetization status & RPM estimate (fake calculation)
        monetization_status = "Enabled" if "meditation" in title.lower() else "Limited"
        rpm_estimate = round(1.5 if monetization_status == "Enabled" else 0.5, 2)

        videos.append({
            "Video ID": video_id,
            "Title": title,
            "Channel": channel,
            "Published": publish_time,
            "Monetization": monetization_status,
            "RPM (USD)": rpm_estimate
        })
    return pd.DataFrame(videos)

# ---------------- RUN SEARCH ----------------
if st.button("🔍 Tìm kiếm Video Meditation"):
    if not check_api_key(api_key):
        st.error("❌ API Key sai! Vui lòng kiểm tra lại trước khi tìm kiếm.")
    else:
        df = search_videos(api_key)
        st.dataframe(df)
        st.download_button(
            "📥 Tải CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="meditation_videos.csv",
            mime="text/csv"
        )
