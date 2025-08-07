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

st.title("🔍 YouTube Niche Finder (Advanced)")
st.markdown("Tìm kiếm từ khóa YouTube đang tăng trưởng dựa trên chủ đề hoặc xu hướng theo từng khu vực.")

# --- FUNCTION: Get YouTube keyword suggestions
@st.cache_data
def get_keyword_suggestions(query):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()[1]
    else:
        return []

# --- FUNCTION: Get Google Trends by region
@st.cache_data
def get_trending_today(region_code='united_states'):
    pytrends = TrendReq(hl='en-US', tz=360)
    try:
        df = pytrends.trending_searches(pn=region_code)
        return df[0].tolist()
    except Exception:
        return []

# --- FUNCTION: Scrape YouTube results
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
        if not video:
            continue
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

# --- FUNCTION: Convert view text to number
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

# --- UI: Select input method
option = st.radio("📥 Chọn nguồn từ khóa", ["Nhập chủ đề thủ công", "Từ Google Trends"])

if option == "Nhập chủ đề thủ công":
    topic = st.text_input("🎯 Nhập chủ đề (ví dụ: ai, crypto, fitness)", value="ai")
    suggestions = get_keyword_suggestions(topic)
else:
    region_map = {
        "🇺🇸 United States": "united_states",
        "🇬🇧 United Kingdom": "united_kingdom",
        "🇪🇺 European Union": "europe",
        "🇦🇺 Australia": "australia",
        "🇻🇳 Vietnam": "vietnam"
    }
    region = st.selectbox("🌍 Chọn khu vực", list(region_map.keys()))
    region_code = region_map[region]
    st.info(f"📈 Lấy từ khóa đang trending tại {region}...")
    trending_keywords = get_trending_today(region_code)
    topic = f"Google Trends - {region}"
    suggestions = trending_keywords[:10]

# --- Advanced options
if suggestions:
    st.subheader("⚙️ Tuỳ chọn nâng cao")
    num_keywords = st.slider("Số lượng từ khóa muốn phân tích", min_value=1, max_value=len(suggestions), value=min(5, len(suggestions)))
    num_videos = st.slider("Số video tối đa mỗi từ khóa", min_value=1, max_value=20, value=10)

    if num_keywords * num_videos > 100:
        st.warning("⚠️ Bạn đang tải rất nhiều dữ liệu. Điều này có thể khiến ứng dụng chạy chậm.")

    st.subheader("📌 Từ khóa được đề xuất")
    st.write(", ".join(suggestions[:num_keywords]))

    st.subheader("📺 Phân tích các video liên quan")
    all_results = []
    for kw in suggestions[:num_keywords]:
        with st.spinner(f"🔎 Đang tìm video cho từ khóa: {kw}"):
            videos = get_video_data(kw, max_results=num_videos)
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
        st.info("⚠️ Không tìm thấy video phù hợp.")
else:
    st.warning("❗ Không tìm thấy từ khóa nào.")
