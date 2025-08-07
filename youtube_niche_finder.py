
import streamlit as st
import pandas as pd
import requests
from googleapiclient.discovery import build
from datetime import datetime

# ==== SETUP ====
st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")
st.title("🔍 YouTube Keyword Analyzer PRO")
st.write("Phân tích từ khóa & video YouTube đang tăng trưởng mạnh mẽ 🚀")

# ==== API KEY ====
api_key = st.secrets["YOUTUBE_API_KEY"]  # Add this to .streamlit/secrets.toml
youtube = build("youtube", "v3", developerKey=api_key)

# ==== INPUT ====
topic = st.text_input("💕 Nhập chủ đề (ví dụ: ai, fitness, crypto)", value="")
country_code = st.selectbox("🌍 Chọn quốc gia (optional)", ["", "US", "VN", "IN", "JP", "KR", "BR", "RU"], index=0)

# ==== FUNCTION ====
def get_suggestions(query):
    suggest_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={query}"
    res = requests.get(suggest_url)
    return res.json()[1]

def search_videos(keyword):
    search_response = youtube.search().list(
        q=keyword,
        part="snippet",
        type="video",
        maxResults=5,
        regionCode=country_code if country_code else None
    ).execute()

    videos = []
    for item in search_response["items"]:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        thumbnail = item["snippet"]["thumbnails"]["high"]["url"]
        published_at = item["snippet"]["publishedAt"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        stats = youtube.videos().list(
            part="statistics,snippet",
            id=video_id
        ).execute()

        view_count = stats["items"][0]["statistics"].get("viewCount", 0)
        published_date = datetime.strptime(published_at[:10], "%Y-%m-%d")
        days_since = max((datetime.now() - published_date).days, 1)
        growth = round(int(view_count) / days_since)

        videos.append({
            "Keyword": keyword,
            "Title": title,
            "Views": int(view_count),
            "Published": published_at[:10],
            "Days Since": days_since,
            "Growth (views/day)": growth,
            "Link": video_url,
            "Thumbnail": thumbnail
        })
    return videos

# ==== MAIN ====
if topic:
    suggestions = get_suggestions(topic)
    st.subheader("📌 Gợi ý từ khóa liên quan:")
    st.write(", ".join(suggestions))

    results = []
    for kw in suggestions[:5]:
        results.extend(search_videos(kw))

    if results:
        df = pd.DataFrame(results)
        st.subheader("📊 Bảng phân tích video")
        st.dataframe(df[["Keyword", "Title", "Views", "Published", "Growth (views/day)", "Link"]])

        st.subheader("🖼️ Thumbnail Gallery")
        for _, row in df.iterrows():
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <img src="{row['Thumbnail']}" width="200" style="margin-right: 10px;" />
                <div>
                    <b>{row['Title']}</b><br>
                    📈 {row['Views']} views • ⏱ {row['Days Since']} days • 🚀 {row['Growth (views/day)']} views/day <br>
                    <a href="{row['Link']}" target="_blank">🔗 Xem video</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Download options
        st.subheader("📥 Tải kết quả")
        csv = df.to_csv(index=False).encode("utf-8")
        excel = df.to_excel(index=False, engine='openpyxl')
        st.download_button("⬇️ Tải CSV", csv, "youtube_data.csv", "text/csv")
        st.download_button("⬇️ Tải Excel", data=excel, file_name="youtube_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("Không tìm thấy video phù hợp.")
