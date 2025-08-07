import streamlit as st
from googleapiclient.discovery import build
import pandas as pd

st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")
st.title("📈 YouTube Keyword Analyzer PRO")
st.markdown("Phân tích từ khóa & video YouTube đang tăng trưởng mạnh mẽ 🚀")

# Nhập API Key từ secrets
api_key = st.secrets["YOUTUBE_API_KEY"]

# Khởi tạo API client
youtube = build("youtube", "v3", developerKey=api_key)

query = st.text_input("🔍 Nhập từ khóa để tìm kiếm:", "fitness")

if "video_data" not in st.session_state:
    st.session_state.video_data = []

def search_videos(query, page_token=None):
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=10,
        order="viewCount",
        regionCode="US",
        relevanceLanguage="en",
        pageToken=page_token,
    )
    return request.execute()

if st.button("📊 Phân tích từ khóa"):
    response = search_videos(query)
    videos = []
    for item in response.get("items", []):
        video_data = {
            "Tiêu đề": item["snippet"]["title"],
            "Kênh": item["snippet"]["channelTitle"],
            "Ngày đăng": item["snippet"]["publishedAt"][:10],
            "Video ID": item["id"]["videoId"],
            "Link": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        }
        videos.append(video_data)
    st.session_state.video_data = videos
    st.session_state.next_page_token = response.get("nextPageToken", None)

if st.button("➕ Tải thêm video YouTube"):
    if st.session_state.get("next_page_token"):
        response = search_videos(query, st.session_state.next_page_token)
        more_videos = []
        for item in response.get("items", []):
            video_data = {
                "Tiêu đề": item["snippet"]["title"],
                "Kênh": item["snippet"]["channelTitle"],
                "Ngày đăng": item["snippet"]["publishedAt"][:10],
                "Video ID": item["id"]["videoId"],
                "Link": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }
            more_videos.append(video_data)
        st.session_state.video_data.extend(more_videos)
        st.session_state.next_page_token = response.get("nextPageToken", None)
    else:
        st.warning("🚫 Không còn video để tải thêm.")

if st.session_state.video_data:
    df = pd.DataFrame(st.session_state.video_data)
    st.dataframe(df, use_container_width=True)

    # Export
    st.download_button("📥 Tải xuống CSV", data=df.to_csv(index=False), file_name="youtube_keywords.csv", mime="text/csv")
    st.download_button("📥 Tải xuống Excel", data=df.to_excel(index=False, engine='openpyxl'), file_name="youtube_keywords.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
