import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime, timedelta
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- STYLES ----------
st.markdown("""
<style>
body, .stApp {
  background-color: #e0f7fa !important;
  color: #0a192f !important;
  font-family: 'Inter', sans-serif;
}
footer { visibility: hidden; }
[data-testid="stSidebar"] {
  background-color: #b3e5fc !important;
  border-right: 1px solid #81d4fa !important;
}
[data-testid="stSidebar"] * {
  color: #0a192f !important;
  font-weight: 500 !important;
}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] select {
  background-color: #ffffff !important;
  color: #0a192f !important;
  border: 1px solid #0277bd !important;
  border-radius: 8px !important;
}
.stButton>button {
  background-color: #0277bd !important;
  color: #ffffff !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
}
.stButton>button:hover {
  background-color: #01579b !important;
}
.stTabs [data-baseweb="tab-list"] button {
  background-color: #b3e5fc !important;
  color: #0a192f !important;
  border-radius: 8px;
}
.stTabs [aria-selected="true"] {
  background-color: #81d4fa !important;
  color: #003366 !important;
  border: 1px solid #0277bd40 !important;
}
.leaflet-container {
  background: #f5f5f5 !important;
  border-radius: 12px !important;
  min-height: 520px !important;
}
[data-testid="stChatInput"] textarea {
  background-color: #ffffff !important;
  color: #0a192f !important;
  border: 1px solid #0277bd !important;
  border-radius: 10px !important;
}
@media (max-width:768px) {
  .leaflet-container { min-height: 420px !important; }
  body { font-size: 15px !important; }
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Final 2026")
st.caption("💻 Zahid Hasan | Gemini Flash + BWDB Mock + Map + Chatbot + Smart Alerts")

# ---------- SESSION STATE INITIAL ----------
if 'risk' not in st.session_state:
    st.session_state.risk = "N/A"
if 'ai_summary' not in st.session_state:
    st.session_state.ai_summary = None
if 'audio' not in st.session_state:
    st.session_state.audio = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# ---------- GEMINI INIT ----------
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")

gemini = init_gemini()

# ---------- MOCK DATA FUNCTIONS ----------
@st.cache_data(ttl=300)
def get_bwdb():
    f = np.random.uniform(-0.5, 0.5)
    return {
        "rivers": [
            {"name": "Padma", "station": "Goalundo", "level": round(8.4 + f, 2), "danger": 10.5, "loc": [23.75, 89.75]},
            {"name": "Jamuna", "station": "Sirajganj", "level": round(9.0 + f, 2), "danger": 11.0, "loc": [24.45, 89.70]},
            {"name": "Meghna", "station": "Ashuganj", "level": round(7.6 + f, 2), "danger": 9.2, "loc": [24.02, 91.00]},
        ]
    }

@st.cache_data(ttl=300)
def get_dashboard_data():
    days = 30
    dates = pd.date_range(datetime.now() - timedelta(days=days-1), periods=days)
    rain_vals = np.clip(50 + 30 * np.sin(np.linspace(0, 3, days)) + np.random.normal(0, 10, days), 0, 200)
    df = pd.DataFrame({"Date": dates, "Rainfall (mm)": rain_vals})
    df["Risk"] = df["Rainfall (mm)"].apply(lambda r: "Low" if r < 60 else "Medium" if r < 120 else "High")
    return df

def simple_predict(r, t, h, l):
    score = (r / 100) + (l / 8) + (h / 100) - (t / 40)
    if score > 2:
        return "High"
    elif score > 1:
        return "Medium"
    else:
        return "Low"

# ---------- SIDEBAR INPUTS ----------
st.sidebar.header("📥 Input Parameters")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum  = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level= st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
loc  = st.sidebar.selectbox("📍 Location", ["Dhaka","Sylhet","Rajshahi","Chittagong"])

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    st.session_state.risk = simple_predict(rain, temp, hum, level)
    if gemini:
        try:
            prompt = f"Location {loc}, Rain {rain}mm, River {level}m, Hum {hum}%, Temp {temp}°C. Flood risk {st.session_state.risk}. Give 2 short Bangla safety tips + English translation."
            response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
            summary = response.text.strip()
            st.session_state.ai_summary = summary
            first_line = summary.split("\n")[0] if summary else ""
            if first_line:
                tts = gTTS(first_line, lang="bn")
                buf = BytesIO()
                tts.write_to_fp(buf)
                st.session_state.audio = buf.getvalue()
        except Exception as e:
            st.session_state.ai_summary = f"⚠️ AI summary unavailable ({e})"
            st.session_state.audio = None

# ---------- TABS ----------
tab1, tab2, tab3, tab4 = st.tabs(["🔮 Prediction","📊 Dashboard","🗺️ Map","💬 Chatbot"])

# --- Prediction Tab ---
with tab1:
    st.subheader(f"📍 {loc} Flood Forecast")
    risk = st.session_state.risk
    color_map = {"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"}
    color = color_map.get(risk, "#0a192f")
    if risk == "N/A":
        st.info("দয়া করে sidebar থেকে Predict বাটন চাপুন")
    else:
        st.markdown(f"<h3 style='color:{color};'>🌀 {risk} Flood Risk</h3>", unsafe_allow_html=True)
    if st.session_state.ai_summary:
        st.markdown("### 📋 Safety Tips")
        st.markdown(st.session_state.ai_summary)
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3")

# --- Dashboard Tab ---
with tab2:
    st.subheader("📈 30-Day Rainfall & Flood Risk Trend")
    df = get_dashboard_data()
    fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
                  color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
                  title="Rainfall & Flood Risk Trend")
    fig.update_layout(plot_bgcolor="#e0f7fa", paper_bgcolor="#e0f7fa",
                      font_color="#0a192f", title_font_color="#0a192f",
                      xaxis_title="Date", yaxis_title="Rainfall (mm)",
                      xaxis=dict(showgrid=True, gridcolor="#ccc"),
                      yaxis=dict(showgrid=True, gridcolor="#ccc"))
    st.plotly_chart(fig, use_container_width=True)

# --- Map Tab ---
with tab3:
    st.subheader("🗺️ Interactive Flood Risk Map (Bangladesh)")
    bwdb = get_bwdb()
    try:
        m = folium.Map(location=[23.7, 90.4], zoom_start=7, tiles="CartoDB positron")
        heat = []
        for r in bwdb["rivers"]:
            risk_r = "High" if r["level"] > r["danger"] else "Medium" if r["level"] > r["danger"]*0.9 else "Low"
            color_r = {"Low":"green","Medium":"orange","High":"red"}[risk_r]
            folium.Marker(
                r["loc"],
                tooltip=f"{r['name']} – {r['level']} m",
                popup=f"<b>{r['name']}</b><br>Station:{r['station']}<br>Level:{r['level']}m<br>Danger:{r['danger']}m<br>Risk:{risk_r}",
                icon=folium.Icon(color=color_r, icon="tint", prefix="fa")
            ).add_to(m)
            pts = 70 if risk_r=="High" else 50 if risk_r=="Medium" else 30
            heat.extend(np.random.normal(loc=r["loc"], scale=[0.4,0.4], size=(pts,2)).tolist())
        if heat:
            HeatMap(heat, radius=18, blur=15, min_opacity=0.25).add_to(m)
        st_folium(m, width="100%", height=540)
    except Exception as ex:
        st.warning(f"⚠️ Map failed to load ({ex}). Showing fallback.")
        st.image("https://maps.googleapis.com/maps/api/staticmap?center=Bangladesh&zoom=6&size=800x500&maptype=terrain",
                 caption="Fallback Static Map", use_container_width=True)

# --- Chatbot Tab ---
with tab4:
    st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if q := st.chat_input("প্রশ্ন করুন / Ask a question..."):
        st.session_state.messages.append({"role":"user","content":q})
        with st.chat_message("assistant"):
            if gemini:
                try:
                    ans = genai.GenerativeModel("gemini-2.5-flash").generate_content(
                        f"You are FloodGuard AI (Bangladesh flood expert). Answer briefly (<100 words) in Bangla + English: {q}"
                    ).text
                except Exception as e:
                    ans = f"AI Chat unavailable: {e}"
            else:
                ans = "Demo mode active — no API key configured."
            st.markdown(ans)
            st.session_state.messages.append({"role":"assistant","content":ans})
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.experimental_rerun()

# ---------- FOOTER ----------
st.divider()
st.caption("🌊 FloodGuard AI © 2026 | Developed by Zahid Hasan 💻")
