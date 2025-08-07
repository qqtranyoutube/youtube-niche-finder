import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
from io import BytesIO
from googleapiclient.discovery import build
from pytrends.request import TrendReq

# --- API KEY ---

api_key = st.secrets["YOUTUBE_API_KEY"]  # Ensure this is set in .streamlit/secrets.toml
youtube = build("youtube", "v3", developerKey=api_key)

# --- PAGE CONFIG ---
st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")
st.title("🚀 YouTube Keyword Analyzer PRO")
st.write("Phân tích từ khóa & video YouTube đang tăng trưởng mạnh mẽ")

# --- INPUT ---
topic = st.text_input("📥 Nhập chủ đề (ví dụ: fitness, ai, sleep)", "")

# --- COLLECT SUGGESTIONS ---
def get_suggestions(topic):
    suggestion_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={topic}"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(suggestion_url, headers=headers)
    return res.json()[1]

# --- CRAWL VIDEO DATA ---
def fetch_video_info(keyword):
    url = f"https://www.youtube.com/results?search_query={keyword}"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")
    results = []
    for video in soup.select("#video-title")[:3]:
        title = video.get("title")
        link = "https://www.youtube.com" + video.get("href")
        results.append({"Keyword": keyword, "Title": title, "Link": link})
    return results

# --- GOOGLE TRENDS PYTRENDS ---
def get_trending_keywords_pytrends():
    pytrends = TrendReq(hl='en-US', tz=360)
    pytrends.build_payload(["youtube"], cat=0, timeframe='now 7-d', geo='', gprop='youtube')
    related = pytrends.related_queries()
    if "youtube" in related and related["youtube"]["rising"] is not None:
        return list(related["youtube"]["rising"].head(10)['query'])
    return []

# --- YOUTUBE TRENDING ---
def get_youtube_trending_videos(regionCode="US"):
    trending = youtube.videos().list(
        part="snippet",
        chart="mostPopular",
        maxResults=10,
        regionCode=regionCode
    ).execute()
    keywords = []
    for item in trending.get("items", []):
        title = item["snippet"]["title"]
        keywords.append(title)
    return keywords

# --- PROCESS ---
all_keywords = []
if topic:
    all_keywords += get_suggestions(topic)

if st.checkbox("📈 Tự động lấy từ khóa trending YouTube", value=True):
    all_keywords += get_youtube_trending_videos()

if st.checkbox("📊 Lấy từ khóa rising từ Google Trends", value=True):
    all_keywords += get_trending_keywords_pytrends()

# --- REMOVE DUPLICATES ---
all_keywords = list(dict.fromkeys(all_keywords))
st.write(f"🔑 Tổng số từ khóa thu thập được: {len(all_keywords)}")
st.write(all_keywords)

# --- VIDEO DATA ---
video_data = []
for kw in all_keywords[:10]:
    video_data.extend(fetch_video_info(kw))

# --- FILTER UI ---
st.subheader("🔍 Bộ lọc nâng cao")
kw_filter = st.multiselect("Lọc theo keyword", options=sorted(set([v['Keyword'] for v in video_data])))
if kw_filter:
    video_data = [v for v in video_data if v['Keyword'] in kw_filter]

df = pd.DataFrame(video_data)
st.dataframe(df)

# --- BIỂU ĐỒ ---
if not df.empty:
    fig = px.bar(df, x="Keyword", title="Số lượng video theo keyword")
    st.plotly_chart(fig, use_container_width=True)

# --- DOWNLOAD ---
col1, col2, col3 = st.columns(3)
with col1:
    st.download_button("📥 Tải CSV", data=df.to_csv(index=False), file_name="youtube_keywords.csv", mime="text/csv")
with col2:
    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    st.download_button("📥 Tải Excel", data=output.getvalue(), file_name="youtube_keywords.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with col3:
    st.download_button("🌐 Tải HTML", data=df.to_html(), file_name="youtube_keywords.html", mime="text/html")
