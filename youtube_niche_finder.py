
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from urllib.parse import quote

st.set_page_config(page_title="YouTube Niche Finder", layout="wide")

st.title("🔍 YouTube Niche Finder (MVP)")
st.markdown("Nhập chủ đề gốc và tìm các keyword đang tăng trưởng trên YouTube.")

# Bước 1: Nhập từ khóa gốc
topic = st.text_input("🎯 Nhập chủ đề (ví dụ: ai, fitness, crypto)", value="ai")

# Bước 2: Lấy gợi ý từ khóa từ YouTube Suggest (qua Google Suggest API)
@st.cache_data
def get_keyword_suggestions(query):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()[1]
    else:
        return []

# Bước 3: Lấy thông tin video từ kết quả tìm kiếm YouTube
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

    import json
    data = json.loads(raw_json)
    try:
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

# Main logic
if topic:
    st.subheader("📌 Gợi ý từ khóa liên quan")
    suggestions = get_keyword_suggestions(topic)
    if suggestions:
        st.write(", ".join(suggestions[:10]))
    else:
        st.error("Không lấy được từ khóa gợi ý.")

    st.subheader("📈 Phân tích video theo từ khóa")
    all_results = []
    for kw in suggestions[:5]:
        videos = get_video_data(kw)
        all_results.extend(videos)

    if all_results:
        df = pd.DataFrame(all_results)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Tải kết quả CSV", data=csv, file_name="youtube_niche_results.csv")
    else:
        st.info("Không có dữ liệu video phù hợp.")
