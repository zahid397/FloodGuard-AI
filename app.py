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
st.set_page_config(page_title="FloodGuard AI", page_icon="Wave", layout="wide")

# ---------- THEME ----------
st.markdown("""
<style>
.stApp {
    background-color: #e0f7fa !important;
    color: #0a192f !important;
    font-family: "Inter", sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #b3e5fc !important;
    border-right: 1px solid #81d4fa !important;
}
[data-testid="stSidebar"] * {
    color: #0a192f !important;
    font-weight: 500 !important;
}
div[data-baseweb="select"], div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #0a192f !important;
}
.stButton>button {
    background-color: #0277bd !important;
    color: white !important;
    border-radius: 8px;
    font-weight: 600;
}
.stButton>button:hover {
    background-color: #01579b !important;
}
.leaflet-container {
    height: 520px !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
/* Alerts */
.stSuccess {background:#e8f5e9!important;color:#2e7d32!important;border:1px solid #4caf50!important;}
.stWarning {background:#fff3e0!important;color:#ef6c00!important;border:1px solid #ff9800!important;}
.stError {background:#ffebee!important;color:#c62828!important;border:1px solid #f44336!important;}
h3, h4, h5 { color:#0a192f!important; font-weight:700!important; }
/* Mobile Fix */
@media (max-width:768px){
    body{font-size:14px!important;}
    .stButton>button{font-size:15px!important;padding:8px!important;}
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("Wave FloodGuard AI – Hackathon Final 2026")
st.caption("Zahid Hasan | Gemini Flash + BWDB Mock + HeatMap + Chatbot + Voice Alerts")

# ---------- INIT ----------
for key in ["risk", "ai_summary", "audio", "messages"]:
    if key not in st.session_state:
        st.session_state[key] = "N/A" if key == "risk" else None if key in ["ai_summary", "audio"] else []

# ---------- GEMINI INIT ----------
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            st.success("Gemini 2.5 Flash loaded")
            return model
    except Exception as e:
        st.warning(f"Gemini setup failed: {e}")
    return None

gemini = init_gemini()

# ---------- MOCK DATA ----------
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

def simple_predict(r, t, h, l):
    score = (r/100) + (l/8) + (h/100) - (t/40)
    return "High" if score > 2 else "Medium" if score > 1 else "Low"

# ---------- SIDEBAR ----------
st.sidebar.header("Input Parameters")
rain = st.sidebar.slider("Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("River Level (m)", 0.0, 20.0, 5.0)
loc = st.sidebar.selectbox("Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])

if st.sidebar.button("Predict Flood Risk", use_container_width=True):
    st.session_state.risk = simple_predict(rain, temp, hum, level)
    st.session_state.ai_summary = st.session_state.audio = None
    if gemini:
        try:
            prompt = f"Location {loc}, Rain {rain}mm, River {level}m, Humidity {hum}%, Temp {temp}°C. Flood risk {st.session_state.risk}. Give 2 short Bangla safety tips + English translation."
            res = gemini.generate_content(prompt)
            text = res.text.strip()
            st.session_state.ai_summary = text
            short = text.split("\n")[0][:100]
            tts = gTTS(short, lang="bn")
            buf = BytesIO()
            tts.write_to_fp(buf)
            st.session_state.audio = buf.getvalue()
        except Exception as e:
            st.session_state.ai_summary = f"AI error: {e}"

# ---------- TABS ----------
tab1, tab2, tab3, tab4 = st.tabs(["Prediction", "Dashboard", "Map", "Chatbot"])

# --- TAB 1 ---
with tab1:
    st.subheader(f"{loc} Flood Forecast")
    color_map = {"Low": "#4caf50", "Medium": "#ff9800", "High": "#f44336"}
    color = color_map.get(st.session_state.risk, "#0a192f")
    if st.session_state.risk == "N/A":
        st.info("Predict বাটন চাপুন (sidebar)")
    else:
        st.markdown(f"<h3 style='color:{color};'>{st.session_state.risk} Flood Risk</h3>", unsafe_allow_html=True)
        if st.session_state.risk == "High":
            st.error("HIGH RISK! Move to higher ground immediately.")
        elif st.session_state.risk == "Medium":
            st.warning("Moderate risk — Stay alert.")
        else:
            st.success("Low risk — Safe conditions.")
    if st.session_state.ai_summary:
        st.markdown("### Safety Tips")
        st.write(st.session_state.ai_summary)
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3")

# --- TAB 2 ---
with tab2:
    st.subheader("30-Day Rainfall & Risk Trend")
    days = 30
    dates = pd.date_range(datetime.now() - timedelta(days=days-1), periods=days)
    rain = np.clip(50 + 30*np.sin(np.linspace(0, 3, days)) + np.random.normal(0, 10, days), 0, 200)
    risk = ["Low" if r < 60 else "Medium" if r < 120 else "High" for r in rain]
    df = pd.DataFrame({"Date": dates, "Rainfall (mm)": rain, "Risk": risk})
    fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
                  color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
                  title="Rainfall & Flood Risk Trend")
    fig.update_layout(plot_bgcolor="#f5f5f5", paper_bgcolor="#f5f5f5")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("NASA GPM Rainfall Data (Real-Time)"):
        st.markdown("[View NASA GPM IMERG →](https://gpm.nasa.gov/data/realtime)")

# --- TAB 3 ---
with tab3:
    st.subheader("Interactive Flood Risk Map")
    try:
        bwdb = get_bwdb()
        m = folium.Map(location=[23.7, 90.4], zoom_start=7, tiles="CartoDB positron")
        heat_data = []
        for r in bwdb["rivers"]:
            risk = "High" if r["level"] > r["danger"] else "Medium" if r["level"] > r["danger"]*0.9 else "Low"
            icon_color = {"Low":"green", "Medium":"orange", "High":"red"}[risk]
            folium.Marker(
                r["loc"],
                tooltip=f"{r['name']} ({r['level']}m)",
                popup=f"<b>{r['name']}</b><br>Station: {r['station']}<br>Level: {r['level']}m<br>Danger: {r['danger']}m<br>Risk: {risk}",
                icon=folium.Icon(color=icon_color, icon="tint", prefix="fa")
            ).add_to(m)
            intensity = 70 if risk == "High" else 50 if risk == "Medium" else 30
            heat_data.extend(np.random.normal(loc=r["loc"], scale=[0.3, 0.3], size=(intensity, 2)).tolist())
        HeatMap(heat_data, radius=20, blur=15, min_opacity=0.3,
                gradient={0.2: '#4caf50', 0.5: '#ff9800', 0.8: '#f44336'}).add_to(m)
        st_folium(m, key="map", width="100%", height=520)
    except Exception as e:
        st.error(f"Map error: {e}")

# --- TAB 4 ---
with tab4:
    st.subheader("FloodGuard AI Chatbot (Bangla + English)")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if q := st.chat_input("Ask a question / প্রশ্ন করুন..."):
        st.session_state.messages.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            if gemini:
                try:
                    reply = gemini.generate_content(
                        f"You are FloodGuard AI (Bangladesh flood expert). Reply briefly in Bangla + English: {q}"
                    ).text
                except Exception as e:
                    reply = f"AI error: {e}"
            else:
                reply = "Demo mode — Gemini API key missing."
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        # Auto-clear old messages
        if len(st.session_state.messages) > 16:
            st.session_state.messages = st.session_state.messages[-16:]
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ---------- FOOTER ----------
st.divider()
st.caption("Wave FloodGuard AI © 2026 | Developed by Zahid Hasan | [GitHub](https://github.com/zahid397/FloodGuard-AI)")
