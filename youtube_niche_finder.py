import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import requests

st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")

api_key = st.secrets["AIzaSyDz_oDmVpRY1T1W-dizavhpQqaIWwdMVrg"]

st.title("🎯 YouTube Keyword Analyzer PRO")
st.write("Phân tích từ khóa & video YouTube đang tăng trưởng mạnh mẽ 🚀")

keyword = st.text_input("🔍 Nhập từ khóa chủ đề YouTube:", value="ai")

def get_keyword_suggestions(query):
    try:
        suggest_url = "http://suggestqueries.google.com/complete/search"
        params = {"client": "firefox", "ds": "yt", "q": query}
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(suggest_url, params=params, headers=headers)
        return response.json()[1]
    except Exception as e:
        st.error(f"Lỗi gợi ý từ khóa: {e}")
        return []

def search_youtube_videos(query, max_results=5):
    youtube = build("youtube", "v3", developerKey=api_key)
    request = youtube.search().list(
        q=query, part="snippet", type="video", maxResults=max_results, order="date"
    )
    response = request.execute()
    videos = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        published = item["snippet"]["publishedAt"][:10]
        channel = item["snippet"]["channelTitle"]
        thumb = item["snippet"]["thumbnails"]["high"]["url"]
        link = f"https://www.youtube.com/watch?v={video_id}"
        videos.append({
            "Keyword": query,
            "Title": title,
            "Channel": channel,
            "Published": published,
            "Link": link,
            "Thumbnail": thumb
        })
    return videos

if keyword:
    st.subheader("📌 Gợi ý từ khóa")
    suggestions = get_keyword_suggestions(keyword)
    st.write(", ".join(suggestions))

    st.subheader("📊 Phân tích video")
    all_videos = []
    for kw in suggestions[:5]:
        all_videos.extend(search_youtube_videos(kw, 5))

    if all_videos:
        df = pd.DataFrame(all_videos)
        st.dataframe(df[["Keyword", "Title", "Channel", "Published", "Link"]])

        st.subheader("🎬 Thumbnails")
        for _, row in df.iterrows():
            st.markdown(f"**{row['Title']}** ({row['Published']})")
            st.image(row["Thumbnail"], width=400)
            st.markdown(f"[🔗 Xem video]({row['Link']})")
            st.markdown("---")

        # Xuất CSV
        st.download_button("📄 Tải CSV", df.to_csv(index=False).encode("utf-8"), "youtube_keywords.csv", "text/csv")
    else:
        st.warning("Không tìm thấy video nào.")
