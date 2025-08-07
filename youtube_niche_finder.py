# youtube_niche_finder.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from urllib.parse import quote
from pytrends.request import TrendReq
import matplotlib.pyplot as plt
import json

st.set_page_config(page_title="YouTube Niche Finder", layout="wide")

st.title("🔍 YouTube Niche Finder (MVP)")
st.markdown("Khám phá các từ khóa YouTube đang tăng trưởng mạnh – từ chủ đề bạn nhập hoặc từ Google Trends.")

# --- FUNCTION: Get Google Suggest (YouTube)
@st.cache_data
def get_keyword_suggestions(query):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()[1]
    else:
        return []

# --- FUNCTION: Get trending keywords today from Google Trends
@st.cache_data
def get_trending_today(country='vietnam'):
    pytrends = TrendReq(hl='vi-VN', tz=360)
    try:
        df = pytrends.trending_searches(pn=country)
        return df[0].tolist()
    except Exception as e:
        return []

# --- FUNCTION: Scrape YouTube search results (basic)
def get_video_data(keyword, max_results=5):
    search_url = f"https://www.youtube.com/results?search_query={quote(keyword)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    scripts = soup.find_all("script")

    for script in scripts:
        if 'var ytInitialData' in script.text:
            raw_json = script.text.strip().split(' = ', 1)[1].rsplit(";", 1)[0]
            break
    else:
        return []

    try:
        data = json.loads(raw_json)
        items = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
    except:
        return []

    results = []
    for item in items:
        video = item.get("videoRenderer")
        if not video: continue
        title = video['title']['runs'][0]['text']
        views_text = video.get("viewCountText", {}).get("simpleText", "0 views")
        published = video.get("publishedTimeText", {}).get("simpleText", "N/A")
        video_id = video["videoId"]
        link = f"https://www.youtube.com/watch?v={video_id}"
        results.append({
            "Keyword": keyword,
            "Title": title,
            "Views": views_text,
            "Published": published,
            "Link": link
        })
        if len(results) >= max_results:
            break
    return results

# --- FUNCTION: Parse view text to number
def parse_views(view_text):
    try:
        if "N/A" in view_text:
            return 0
        view_text = view_text.lower().replace("views", "").strip()
        if "tr" in view_text:
            return float(view_text.replace("tr", "").strip()) * 1_000_000
        elif "k" in view_text:
            return float(view_text.replace("k", "").strip()) * 1_000
        else:
            return int(view_text.replace(",", ""))
    except:
        return 0

# --- UI CHOICE: Input source
option = st.radio("📥 Chọn nguồn từ khóa", ["Nhập thủ công", "Từ Google Trends (VN)"])

if option == "Nhập thủ công":
    topic = st.text_input("🎯 Nhập chủ đề (ví dụ: ai, fitness, crypto)", value="ai")
    suggestions = get_keyword_suggestions(topic)
else:
    st.info("📈 Lấy từ khóa thịnh hành hôm nay tại Việt Nam...")
    trending_keywords = get_trending_today()
    topic = "Google Trends"
    suggestions = trending_keywords[:10]

# --- MAIN LOGIC
if suggestions:
    st.subheader("📌 Danh sách từ khóa liên quan")
    st.write(", ".join(suggestions))

    st.subheader("📈 Phân tích video theo từ khóa")
    all_results = []
    for kw in suggestions[:5]:  # lấy 5 từ khóa đầu tiên để phân tích
        with st.spinner(f"🔎 Đang phân tích: {kw}..."):
            videos = get_video_data(kw)
        all_results.extend(videos)

    if all_results:
        df = pd.DataFrame(all_results)
        df["ParsedViews"] = df["Views"].apply(parse_views)
        df["Published"] = df["Published"].fillna("N/A")

        st.dataframe(df.drop(columns=["ParsedViews"]), use_container_width=True)

        # --- Chart
        st.subheader("📊 Biểu đồ lượt xem trung bình theo từ khóa")
        chart_df = df.groupby("Keyword")["ParsedViews"].mean().sort_values(ascending=False)
        st.bar_chart(chart_df)

        # --- Download CSV
        csv = df.drop(columns=["ParsedViews"]).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Tải kết quả CSV", data=csv, file_name="youtube_niche_results.csv", mime="text/csv")
    else:
        st.info("⚠️ Không có dữ liệu video phù hợp.")
else:
    st.warning("❗ Không tìm thấy từ khóa gợi ý.")
