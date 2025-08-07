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
topic = st.text_input("🧠 Nhập chủ đề (ví dụ: fitness, ai, sleep)", "")

# --- CHECKBOXES ---
use_trending = st.checkbox("📝 Tự động lấy từ khóa trending YouTube", value=True)
use_google_trends = st.checkbox("📈 Lấy từ khóa rising từ Google Trends", value=True)

# --- COLLECT SUGGESTIONS ---
def get_suggestions(topic):
    suggestion_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={topic}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(suggestion_url, headers=headers)
    suggestions = []
    if response.status_code == 200:
        try:
            suggestions = response.json()[1]
        except Exception:
            pass
    return suggestions

# --- COLLECT TRENDING VIDEOS ---
def get_trending_videos():
    request = youtube.videos().list(
        part="snippet",
        chart="mostPopular",
        maxResults=20,
        regionCode="US"
    )
    response = request.execute()
    titles = [item["snippet"]["title"] for item in response.get("items", [])]
    return titles

# --- COLLECT GOOGLE TRENDS ---
def get_google_trends(keyword):
    pytrend = TrendReq()
    pytrend.build_payload([keyword], cat=0, timeframe='now 7-d', geo='US', gprop='youtube')
    related = pytrend.related_queries()[keyword]['rising']
    if related is not None:
        return related['query'].tolist()
    return []

# --- COLLECT ALL KEYWORDS ---
all_keywords = []

if topic:
    all_keywords.extend(get_suggestions(topic))

if use_trending:
    all_keywords.extend(get_trending_videos())

if use_google_trends and topic:
    all_keywords.extend(get_google_trends(topic))

# --- REMOVE DUPLICATES ---
all_keywords = list(set(all_keywords))

st.markdown(f"""
🔑 **Tổng số từ khóa thu thập được: {len(all_keywords)}**
```python
{all_keywords}
```
""")

# --- FILTER ---
st.subheader("🔍 Bộ lọc nâng cao")
selected = st.multiselect("Lọc theo keyword", options=sorted(all_keywords))
filtered = selected if selected else all_keywords

# --- TABLE ---
df = pd.DataFrame(filtered, columns=["Keyword"])
st.dataframe(df, use_container_width=True)

# --- DOWNLOAD ---
buffer = BytesIO()
df.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button("📥 Tải CSV", data=df.to_csv(index=False), file_name="keywords.csv", mime="text/csv")
st.download_button("📥 Tải Excel", data=buffer, file_name="keywords.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.download_button("🌐 Tải HTML", data=df.to_html(index=False), file_name="keywords.html", mime="text/html")
