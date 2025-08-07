import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

st.set_page_config(page_title="YouTube Niche Finder", layout="wide")

st.title("🔍 YouTube Niche Finder (MVP)")
st.write("Nhập chủ đề gốc và tìm các keyword đang tăng trưởng trên YouTube.")

topic = st.text_input("💕 Nhập chủ đề (ví dụ: ai, fitness, crypto)", value="")

# --- PHẦN GỢI Ý KEYWORD ---
if topic:
    st.subheader("📌 Gợi ý từ khóa liên quan")
    suggestion_url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={topic}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(suggestion_url, headers=headers)
    suggestions = response.json()[1]
    st.write(", ".join(suggestions))

    # --- PHÂN TÍCH VIDEO ---
    st.subheader("📈 Phân tích video theo từ khóa ⇔")
    results = []
    for keyword in suggestions[:5]:
        url = f"https://www.youtube.com/results?search_query={keyword}"
        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
        for video in soup.select("a#video-title")[:2]:
            title = video['title']
            link = "https://www.youtube.com" + video['href']
            views = "?"
            published = "?"
            results.append({"Keyword": keyword, "Title": title, "Views": views, "Published": published, "Link": link})

    st.dataframe(pd.DataFrame(results))

    # --- PHẦN 1: GỢI Ý VIDEO IDEA TỪ AI ---
    st.subheader("🤖 Gợi ý ý tưởng video với AI (OpenRouter)")
    openrouter_api_key = st.secrets.get("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", "")

    if openrouter_api_key:
        prompt = f"Tôi muốn làm video YouTube về chủ đề '{topic}'. Hãy gợi ý 5 ý tưởng video hấp dẫn, sáng tạo và có tiềm năng viral."
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "HTTP-Referer": "https://youtube-niche-finder.streamlit.app",
            "Content-Type": "application/json"
        }
        data = {
            "model": "mistral",
            "messages": [{"role": "user", "content": prompt}]
        }
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        ideas = res.json()["choices"][0]["message"]["content"]
        st.markdown(ideas)
    else:
        st.warning("Bạn cần cấu hình `OPENROUTER_API_KEY` trong Streamlit → Secrets để dùng AI.")

    # --- PHẦN 2: GỢI Ý VIDEO IDEA TỪ CSV ---
    st.subheader("📂 Gợi ý ý tưởng video có sẵn")
    try:
        df_ideas = pd.read_csv("video_ideas.csv")
        matched = df_ideas[df_ideas["keyword"].str.contains(topic, case=False)]
        if not matched.empty:
            for i, idea in enumerate(matched["idea"].values):
                st.write(f"{i+1}. {idea}")
        else:
            st.info("Không có ý tưởng phù hợp trong dữ liệu nội bộ.")
    except:
        st.info("Chưa có file `video_ideas.csv`. Tải file vào repo để dùng phần này.")
