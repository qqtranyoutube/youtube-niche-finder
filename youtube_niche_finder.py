# streamlit_app.py
import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd

# Google libs
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ----------------------- CONFIG -----------------------
st.set_page_config(page_title="YouTube Analytics — RPM & Monetization", layout="wide")
st.title("📈 YouTube Analytics — RPM & Monetization (OAuth)")

# ----------------------- HELPERS -----------------------
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

def credentials_to_dict(creds: Credentials):
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }

def build_credentials_from_dict(d: dict):
    return Credentials(
        token=d.get("token"),
        refresh_token=d.get("refresh_token"),
        token_uri=d.get("token_uri"),
        client_id=d.get("client_id"),
        client_secret=d.get("client_secret"),
        scopes=d.get("scopes")
    )

def save_uploaded_client_secrets(uploaded_file):
    """Save uploaded client_secret.json to /tmp/client_secret.json"""
    path = "/tmp/client_secret.json"
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

# ----------------------- UI: Client secret -----------------------
st.sidebar.header("1) Client secret (OAuth)")
st.sidebar.markdown(
    "Upload `client_secret.json` (OAuth 2.0 Client ID, Web application). "
    "Redirect URI must include your Streamlit app URL (or http://localhost:8501 for local)."
)
uploaded = st.sidebar.file_uploader("Upload client_secret.json", type=["json"])

if uploaded:
    client_secrets_file = save_uploaded_client_secrets(uploaded)
    st.sidebar.success("client_secret.json uploaded and saved.")
else:
    client_secrets_file = st.secrets.get("CLIENT_SECRET_PATH")  # optional pre-configured path
    if client_secrets_file:
        st.sidebar.info(f"Using client secret from secrets: {client_secrets_file}")
    else:
        st.sidebar.info("No client_secret.json uploaded yet.")

# ----------------------- UI: Redirect / Auth flow -----------------------
st.sidebar.header("2) OAuth / Authorization")
# Determine redirect URI:
# Prefer user-provided redirect base in secrets, else use page url detection (best-effort)
app_url = st.secrets.get("APP_URL", "")  # optional: set your app URL in streamlit secrets
if not app_url:
    # try to guess (works locally)
    app_url = st.experimental_get_query_params().get("app_url", [""])[0] or ""
if app_url:
    st.sidebar.write("App Redirect base detected.")
redirect_base = app_url or st.text_input("Enter your App Redirect URI base (e.g. http://localhost:8501)", value="")

# session state: store creds dict
if "creds" not in st.session_state:
    st.session_state.creds = None

# Create auth URL and show link
if client_secrets_file and redirect_base:
    try:
        redirect_uri = redirect_base.rstrip("/") + "/?auth_callback=1"  # we'll check query param
        flow = Flow.from_client_secrets_file(
            client_secrets_file=client_secrets_file,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        auth_url, _ = flow.authorization_url(prompt="consent", include_granted_scopes="true")
        st.sidebar.markdown(f"[🔐 Click to authorize]({auth_url}) (opens Google consent screen)")
        st.sidebar.caption("After authorizing, you'll be redirected back to the app URL. Make sure redirect_uri set in Google Console matches this app URL.")
    except Exception as e:
        st.sidebar.error(f"Error creating authorization URL: {e}")
else:
    st.sidebar.info("Upload client_secret.json and set redirect base to create auth link.")

# ----------------------- Handle OAuth callback (exchange code) -----------------------
# When user is redirected back, Google appends 'code' to query params.
params = st.experimental_get_query_params()
if "code" in params and client_secrets_file and redirect_base:
    # Exchange code for tokens
    code = params["code"][0]
    try:
        redirect_uri = redirect_base.rstrip("/") + "/?auth_callback=1"
        flow = Flow.from_client_secrets_file(
            client_secrets_file=client_secrets_file,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        flow.fetch_token(code=code)
        creds = flow.credentials
        st.session_state.creds = credentials_to_dict(creds)
        st.success("✅ Authorization successful. Credentials saved in session.")
        # Clear code param to avoid reprocessing on rerun (user can remove manually or refresh)
    except Exception as e:
        st.error(f"❌ Error exchanging code for token: {e}")

# ----------------------- Option to paste redirect full URL (fallback) -----------------------
st.sidebar.markdown("---")
st.sidebar.markdown("**Fallback:** If redirect doesn't return to Streamlit, paste the full redirect URL you got from Google (it contains `code=`).")
redirect_full = st.sidebar.text_input("Paste full redirect URL (optional)")

if redirect_full and "code=" in redirect_full:
    # extract code
    import urllib.parse as up
    qs = up.urlparse(redirect_full).query
    qd = up.parse_qs(qs)
    if "code" in qd:
        code = qd["code"][0]
        try:
            redirect_uri = redirect_base.rstrip("/") + "/?auth_callback=1"
            flow = Flow.from_client_secrets_file(
                client_secrets_file=client_secrets_file,
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            flow.fetch_token(code=code)
            creds = flow.credentials
            st.session_state.creds = credentials_to_dict(creds)
            st.success("✅ Authorization successful via pasted URL. Credentials saved.")
        except Exception as e:
            st.error(f"❌ Error exchanging code (pasted URL): {e}")

# ----------------------- Check credential / show account -----------------------
def creds_valid_and_build():
    if not st.session_state.creds:
        st.info("🔒 Chưa xác thực. Hãy upload client_secret.json và authorize.")
        return None, None
    try:
        creds = build_credentials_from_dict(st.session_state.creds)
        # Refresh token if needed
        if creds.expired and creds.refresh_token:
            creds.refresh(Request=None)  # google oauth library will handle; Request=None is accepted in many contexts
        # Build service clients
        youtube = build("youtube", "v3", credentials=creds)
        analytics = build("youtubeAnalytics", "v2", credentials=creds)
        return youtube, analytics
    except Exception as e:
        st.error(f"❌ Lỗi credentials: {e}")
        return None, None

youtube_client, analytics_client = creds_valid_and_build()

# ----------------------- Main UI: choose date range & fetch -----------------------
st.header("3) Phân tích RPM & Monetization (kênh đã xác thực)")

col1, col2 = st.columns(2)
with col1:
    days = st.slider("Khoảng thời gian (ngày)", 7, 180, 28)
with col2:
    max_videos = st.slider("Số video lấy dữ liệu (top theo views)", 1, 50, 20)

end_date = datetime.utcnow().date()
start_date = end_date - timedelta(days=days)

st.markdown(f"**Khoảng thời gian**: {start_date} → {end_date}")

if st.button("🔎 Lấy dữ liệu RPM & Monetization"):
    if not youtube_client or not analytics_client:
        st.error("⚠️ Chưa xác thực credentials. Vui lòng hoàn tất OAuth.")
    else:
        with st.spinner("Đang gọi YouTube Analytics API..."):
            try:
                # 1) Query analytics: estimatedRevenue & views grouped by video
                # ids='channel==MINE' uses authenticated channel
                resp = analytics_client.reports().query(
                    ids="channel==MINE",
                    startDate=str(start_date),
                    endDate=str(end_date),
                    metrics="estimatedRevenue,views",
                    dimensions="video",
                    sort="-views",
                    maxResults=max_videos
                ).execute()
                rows = resp.get("rows", [])
                # rows: [[videoId, revenue, views], ...]  (note ordering: as requested, dims then metrics)
                data = []
                video_ids = []
                for r in rows:
                    vid = r[0]
                    revenue = float(r[1]) if r[1] is not None else 0.0
                    views = int(r[2]) if r[2] is not None else 0
                    rpm = (revenue / views * 1000) if views > 0 else 0.0
                    data.append({"videoId": vid, "estimatedRevenue": revenue, "views": views, "rpm": round(rpm, 2)})
                    video_ids.append(vid)

                # 2) Enrich with Data API (title, channel, monetizationDetails if available)
                if video_ids:
                    # API accepts comma-separated list (max 50)
                    vids_str = ",".join(video_ids)
                    video_resp = youtube_client.videos().list(
                        part="snippet,statistics,monetizationDetails,status",
                        id=vids_str,
                        maxResults=len(video_ids)
                    ).execute()
                    # Map by id
                    info_map = {}
                    for item in video_resp.get("items", []):
                        vid = item["id"]
                        title = item["snippet"].get("title")
                        channel_title = item["snippet"].get("channelTitle")
                        # monetizationDetails may exist only for authorized owners
                        monet_details = item.get("monetizationDetails", {})
                        monet_status = None
                        # Attempt to infer monetization:
                        if monet_details:
                            # monetizationDetails may contain 'access' or other fields; treat presence as monetized
                            monet_status = "Monetized (owner info)"
                        else:
                            monet_status = "Unknown (need owner data)"
                        info_map[vid] = {
                            "title": title,
                            "channel": channel_title,
                            "monet_status": monet_status,
                            "stat_views": int(item.get("statistics", {}).get("viewCount", 0))
                        }
                else:
                    info_map = {}

                # 3) Combine into DataFrame
                records = []
                for d in data:
                    vid = d["videoId"]
                    info = info_map.get(vid, {})
                    records.append({
                        "Video ID": vid,
                        "Title": info.get("title", vid),
                        "Channel": info.get("channel", ""),
                        "Views (period)": d["views"],
                        "Estimated Revenue (USD)": d["estimatedRevenue"],
                        "RPM (USD)": d["rpm"],
                        "Monetization Info": info.get("monet_status", "Unknown")
                    })

                df = pd.DataFrame(records).sort_values(by="Views (period)", ascending=False)
                st.success(f"Đã lấy dữ liệu cho {len(df)} videos.")
                st.dataframe(df, use_container_width=True)

                # Download buttons
                st.download_button("📥 Tải CSV", df.to_csv(index=False).encode("utf-8"), file_name="youtube_rpm.csv", mime="text/csv")
                st.download_button("📥 Tải Excel", df.to_excel(index=False, engine="openpyxl"), file_name="youtube_rpm.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except HttpError as e:
                try:
                    err = json.loads(e.content.decode())
                    st.error(f"API Error {e.resp.status}: {err.get('error', {}).get('message')}")
                except Exception:
                    st.error(f"HttpError: {e}")
            except Exception as e:
                st.error(f"Lỗi khi lấy dữ liệu: {e}")
