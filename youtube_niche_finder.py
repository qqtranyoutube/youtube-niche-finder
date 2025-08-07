import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import googleapiclient.discovery

# ✅ Lấy API key từ secrets
youtube_api_key = st.secrets["youtube_api_key"]

st.set_page_config(page_title="YouTube Niche Finder", layout="wide")

st.title("🔍 YouTube Niche Finder (MVP)")
st.write("Nhập chủ đề gốc và tìm các keyword đang tăng trưởng trên YouTube.")

# Nhập chủ đề
topic = st.text_input("💕 Nhập chủ đề (ví dụ: ai, fitness, crypto)", value="")

# === PHẦN GỢI Ý KEYWORD ===
if topic:
    st.subheader("📌 Gợi ý từ khóa liên quan")
    suggestion_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={topic}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(suggestion_url, headers=headers)
    suggestions = response.json()[1]
    st.write("➡️", ", ".join(suggestions))

    # === PHÂN TÍCH VIDEO ===
    st.subheader("📄 Phân tích video theo từ khóa ➼")
    results = []
    for keyword in suggestions[:5]:
        url = f"https://www.youtube.com/results?search_query={keyword}"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
        for video in soup.select("#video-title")[:2]:
            title = video.get('title', 'No title')
            link = "https://www.youtube.com" + video.get('href', '')
            results.append({
                "Keyword": keyword,
                "Title": title,
                "Views": "?",  # Placeholder
                "Published": "?",
                "Link": link
            })
    st.dataframe(pd.DataFrame(results))
