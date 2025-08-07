import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pytrends.request import TrendReq
from io import BytesIO

# === SETUP ===
st.set_page_config(page_title="YouTube Niche Finder (Pro)", layout="wide")
st.title("🔍 YouTube Niche Finder (Pro Edition)")
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
