import streamlit as st
import pandas as pd
import altair as alt
import requests
from io import BytesIO
from PIL import Image
import base64
from youtube_transcript_api import YouTubeTranscriptApi
import plotly.express as px
import matplotlib.pyplot as plt
from io import BytesIO
import xlsxwriter
import re

st.set_page_config(page_title="YouTube Keyword Analyzer PRO", layout="wide")
st.title("🔍 YouTube Keyword Analyzer PRO")

uploaded_file = st.file_uploader("📤 Tải lên file Excel chứa danh sách từ khóa", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    keywords = df.iloc[:, 0].dropna().tolist()

    results = []
    for keyword in keywords:
        query = keyword.replace(' ', '+')
        url = f"https://www.youtube.com/results?search_query={query}"
        results.append({"Keyword": keyword, "Search URL": url})

    df_result = pd.DataFrame(results)
    st.success("✅ Đã phân tích xong từ khóa!")

    tab1, tab2, tab3 = st.tabs(["📈 Biểu đồ", "📋 Danh sách", "📊 Xu hướng"])

    with tab1:
        st.subheader("🔍 Từ khóa đã phân tích")
        chart_data = pd.DataFrame({"Keyword": [r["Keyword"] for r in results]})
        st.bar_chart(chart_data.value_counts(), use_container_width=True)

    with tab2:
        st.subheader("📋 Danh sách từ khóa và link tìm kiếm YouTube")
        st.dataframe(df_result, use_container_width=True)

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_result.to_excel(writer, index=False)
            writer.save()
        st.download_button(
            "📥 Tải Excel",
            data=buffer.getvalue(),
            file_name="keywords.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with tab3:
        st.subheader("📊 Video Trending Phân Tích")

        trending_videos = [
            {
                "title": "Kodak Black - Identity Theft [Official Music Video]",
                "thumbnail": "https://i.ytimg.com/vi/abc12345678/hqdefault.jpg",
                "views": "191,428",
                "channel": "Kodak Black"
            },
            {
                "title": "Fortnite Battle Royale Chapter 6 Season 4: Shock 'N Awesome | Launch Trailer",
                "thumbnail": "https://i.ytimg.com/vi/def98765432/hqdefault.jpg",
                "views": "1,656,883",
                "channel": "Fortnite"
            },
            {
                "title": "the #1 CONTROLLER PLAYER on WARZONE into NEW BATTLEFIELD (giveaways all night)",
                "thumbnail": "https://i.ytimg.com/vi/ghi56789123/hqdefault.jpg",
                "views": "287,757",
                "channel": "Lucky Chamu"
            },
            {
                "title": "Justin Bieber - YUKON",
                "thumbnail": "https://i.ytimg.com/vi/jkl34567891/hqdefault.jpg",
                "views": "3,271,022",
                "channel": "Justin Bieber"
            }
        ]

        columns = st.columns(4)
        for i, video in enumerate(trending_videos):
            with columns[i % 4]:
                st.image(video["thumbnail"], caption=f"{video['title']} 👁 {video['views']} | 📺 {video['channel']}", use_container_width=True)
