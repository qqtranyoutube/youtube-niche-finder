import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from googleapiclient.discovery import build
import io

# === Cấu hình trang ===
st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")
st.title("🚀 YouTube Keyword Analyzer PRO")
st.write("Phân tích từ khóa & video YouTube đang tăng trưởng mạnh mẽ")

# === Nhập API Key ===
api_key = st.secrets["YOUTUBE_API_KEY"]
youtube = build("youtube", "v3", developerKey=api_key)

# === Nhập chủ đề ===
topic = st.text_input("🔎 Nhập chủ đề (ví dụ: ai, fitness, crypto)", value="")

# === Phân tích từ khóa và video ===
df = pd.DataFrame()
if topic:
    st.subheader("📌 Gợi ý từ khóa liên quan")
    suggestion_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={topic}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(suggestion_url, headers=headers)
    suggestions = response.json()[1]
    st.write("➡️", ", ".join(suggestions))

    st.subheader("📄 Phân tích video theo từ khóa")
    all_results = []

    for keyword in suggestions[:5]:
        search_response = youtube.search().list(
            q=keyword,
            part="snippet",
            maxResults=5,
            type="video",
            order="viewCount"
        ).execute()

        for item in search_response["items"]:
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            published = item["snippet"]["publishedAt"][:10]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            video_response = youtube.videos().list(
                part="statistics",
                id=video_id
            ).execute()

            stats = video_response["items"][0]["statistics"]
            views = stats.get("viewCount", "0")

            all_results.append({
                "Keyword": keyword,
                "Title": title,
                "Views": f"{int(views):,} views",
                "Published": published,
                "Link": f"https://www.youtube.com/watch?v={video_id}"
            })

    df = pd.DataFrame(all_results)
    st.dataframe(df)

    # === 📥 Xuất Excel, CSV ===
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    st.download_button("📥 Tải xuống Excel", data=buffer.getvalue(), file_name="youtube_keywords.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("📥 Tải xuống CSV", data=df.to_csv(index=False), file_name="youtube_keywords.csv", mime="text/csv")

    # === 📊 Biểu đồ thống kê ===
    st.subheader("📈 Thống kê nhanh")
    chart_data = df.copy()
    chart_data["Views"] = chart_data["Views"].str.replace("views", "").str.replace(",", "").str.strip()
    chart_data["Views"] = pd.to_numeric(chart_data["Views"], errors="coerce")
    chart_data = chart_data.dropna(subset=["Views"])
    chart_data = chart_data.sort_values(by="Views", ascending=False)
    st.bar_chart(chart_data[["Title", "Views"]].set_index("Title"))

    # === 🔍 Bộ lọc nâng cao ===
    st.subheader("🔍 Lọc nâng cao")
    selected_keyword = st.selectbox("Chọn keyword", options=["Tất cả"] + sorted(df["Keyword"].unique().tolist()))
    if selected_keyword != "Tất cả":
        df_filtered = df[df["Keyword"] == selected_keyword]
    else:
        df_filtered = df

    st.dataframe(df_filtered)

    # === 📤 Xuất HTML ===
    st.subheader("🌐 Tải xuống HTML")
    html_data = df_filtered.to_html(index=False, escape=False)
    st.download_button("📥 Tải xuống HTML", data=html_data, file_name="youtube_keywords.html", mime="text/html")
