import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pytrends.request import TrendReq

# === SETUP ===
st.set_page_config(page_title="YouTube Niche Finder (Advanced)", layout="wide")
st.title("🔍 YouTube Niche Finder (Advanced + Load More)")
st.write("Khám phá từ khóa YouTube đang tăng trưởng theo chủ đề hoặc xu hướng quốc tế.")

# === CHỌN NGUỒN TỪ KHÓA ===
source = st.radio("🧭 Chọn nguồn từ khóa", ["Nhập chủ đề thủ công", "Từ Google Trends"], index=0)

topic = ""
keywords = []

# === CHẾ ĐỘ 1: NHẬP TAY ===
if source == "Nhập chủ đề thủ công":
    topic = st.text_input("💕 Nhập chủ đề (ví dụ: ai, fitness, crypto)", value="")
    if topic:
        st.subheader("📌 Gợi ý từ khóa liên quan")
        suggestion_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={topic}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(suggestion_url, headers=headers)
        suggestions = response.json()[1]
        st.success("✅ Gợi ý từ khóa:")
        st.write(", ".join(suggestions))
        keywords = suggestions[:5]

# === CHẾ ĐỘ 2: GOOGLE TRENDS ===
elif source == "Từ Google Trends":
    st.subheader("🌍 Chọn khu vực để lấy xu hướng")
    regions = {
        "United States": "united_states",
        "Vietnam": "vietnam",
        "Japan": "japan",
        "United Kingdom": "united_kingdom",
        "India": "india",
        "Germany": "germany",
        "South Korea": "south_korea",
    }
    region_name = st.selectbox("🌐 Quốc gia", list(regions.keys()))
    region_code = regions[region_name]

    st.info(f"📈 Đang lấy từ khóa trending tại 🇺🇸 {region_name}...")
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        trending_df = pytrends.trending_searches(pn=region_code)
        if trending_df.empty:
            st.warning("❗ Không có từ khóa.")
        else:
            keywords = trending_df[0].tolist()[:5]
            st.success("✅ Từ khóa trending:")
            st.write(", ".join(keywords))
    except Exception as e:
        st.error(f"🚫 Lỗi khi lấy dữ liệu từ Google Trends: {e}")

# === PHÂN TÍCH VIDEO YOUTUBE ===
if keywords:
    st.subheader("📄 Phân tích video trên YouTube")
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    for keyword in keywords:
        url = f"https://www.youtube.com/results?search_query={keyword}"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
        for video in soup.select("#video-title")[:2]:
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
