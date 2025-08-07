
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from googleapiclient.discovery import build
import io

# Cấu hình trang
st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")

st.title("📈 YouTube Keyword Analyzer PRO")
st.write("Phân tích từ khóa & video YouTube đang tăng trưởng mạnh mẽ 🚀")

# Lấy API key từ secrets
api_key = st.secrets["YOUTUBE_API_KEY"]
youtube = build("youtube", "v3", developerKey=api_key)

# Nhập chủ đề gốc
topic = st.text_input("🔍 Nhập chủ đề (ví dụ: ai, fitness, crypto)", value="")

if topic:
    # === GỢI Ý TỪ KHÓA ===
    st.subheader("📌 Gợi ý từ khóa")
    suggest_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={topic}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(suggest_url, headers=headers)
    suggestions = response.json()[1]
    st.write("➡️", ", ".join(suggestions))

    # === PHÂN TÍCH VIDEO TỪ YOUTUBE DATA API ===
    st.subheader("🎯 Phân tích video")
    results = []

    for keyword in suggestions[:5]:
        search_response = youtube.search().list(
            q=keyword,
            part="snippet",
            type="video",
            maxResults=5,
            order="viewCount"
        ).execute()

        for item in search_response["items"]:
            title = item["snippet"]["title"]
            video_id = item["id"]["videoId"]
            link = f"https://www.youtube.com/watch?v={video_id}"
            channel = item["snippet"]["channelTitle"]
            published = item["snippet"]["publishedAt"]

            results.append({
                "Keyword": keyword,
                "Title": title,
                "Channel": channel,
                "Published": published,
                "Link": link
            })

    df = pd.DataFrame(results)
    st.dataframe(df)

    # Nút tải thêm video
    if st.button("🔄 Tải thêm video YouTube"):
        st.experimental_rerun()

    # Export CSV
    st.download_button(
        "📥 Tải xuống CSV",
        data=df.to_csv(index=False),
        file_name="youtube_keywords.csv",
        mime="text/csv"
    )

    # Export Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    excel_data = excel_buffer.getvalue()

    st.download_button(
        "📥 Tải xuống Excel",
        data=excel_data,
        file_name="youtube_keywords.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
