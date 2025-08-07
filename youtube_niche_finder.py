import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pytrends.request import TrendReq
from io import BytesIO

# === SETUP ===
st.set_page_config(page_title="YouTube Niche Finder (V3)", layout="wide")
st.title("🔍 YouTube Niche Finder (V3 - No API Key Needed)")
st.write("Khám phá từ khóa YouTube đang tăng trưởng theo chủ đề hoặc xu hướng quốc gia.")

# === CHỌN NGUỒN TỪ KHÓA ===
source = st.radio("🧭 Chọn nguồn từ khóa", ["Nhập chủ đề thủ công", "Từ Google Trends"], index=0)

topic = ""
keywords = []

# === CHẾ ĐỘ 1: NHẬP TAY ===
if source == "Nhập chủ đề thủ công":
    topic = st.text_input("💕 Nhập chủ đề (ví dụ: ai, fitness, crypto)", value="")
    if topic:
        st.subheader("📌 Gợi ý từ khóa liên quan (Autocomplete)")
        suggestion_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={topic}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(suggestion_url, headers=headers)
        suggestions = response.json()[1]
        st.success("✅ Gợi ý từ khóa:")
        st.write(", ".join(suggestions))
        keywords = suggestions[:5]

# === CHẾ ĐỘ 2: GOOGLE TRENDS (related_queries) ===
elif source == "Từ Google Trends":
    st.subheader("🌍 Chọn quốc gia & chủ đề để lấy xu hướng")
    countries = {
        "United States": "US",
        "Vietnam": "VN",
        "Japan": "JP",
        "United Kingdom": "GB",
        "India": "IN",
        "Germany": "DE",
        "South Korea": "KR",
    }
    geo_code = countries[st.selectbox("🌐 Quốc gia", list(countries.keys()))]

    topics = ["technology", "fitness", "ai", "music", "crypto", "education", "fashion", "gaming"]
    selected_topic = st.selectbox("🧠 Chọn chủ đề", topics)

    st.info(f"📈 Đang lấy từ khóa tăng trưởng cho chủ đề **{selected_topic}** tại **{geo_code}**...")

    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([selected_topic], cat=0, timeframe='now 7-d', geo=geo_code)
        related = pytrends.related_queries()
        top_keywords = related[selected_topic]["top"]

        if top_keywords is None or top_keywords.empty:
            st.warning("❗ Không có từ khóa liên quan.")
        else:
            keywords = top_keywords["query"].tolist()[:5]
            st.success("✅ Từ khóa đang tăng trưởng:")
            st.write(", ".join(keywords))
    except Exception as e:
        st.error(f"🚫 Lỗi khi lấy dữ liệu từ Google Trends: {e}")

# === CHỌN SỐ LƯỢNG VIDEO ===
num_videos = st.slider("🎥 Số video mỗi từ khóa", min_value=2, max_value=10, value=2)

# === PHÂN TÍCH VIDEO YOUTUBE ===
if keywords:
    st.subheader("📄 Phân tích video trên YouTube")
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    for keyword in keywords:
        url = f"https://www.youtube.com/results?search_query={keyword}"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
        videos = soup.select("#video-title")
        for video in videos[:num_videos]:
            title = video.get('title', 'No title')
            link = "https://www.youtube.com" + video.get('href', '')
            results.append({
                "Keyword": keyword,
                "Title": title,
                "Views": "?",
                "Published": "?",
                "Link": link
            })

    df = pd.DataFrame(results)
    st.dataframe(df)

    # === XUẤT FILE ===
    st.subheader("📤 Tải kết quả")
    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Tải CSV", data=csv, file_name="youtube_keywords.csv", mime="text/csv")

    with col2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='YouTube Keywords')
        st.download_button("⬇️ Tải Excel", data=output.getvalue(), file_name="youtube_keywords.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
