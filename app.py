import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import joblib
import requests
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- THEME ----------
st.markdown("""
<style>
.stApp {background-color:#ffffff!important;color:#1a1a1a!important;font-family:"Segoe UI",sans-serif!important;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#0078d7,#0099ff)!important;border-right:3px solid #005a9e!important;}
[data-testid="stSidebar"] * {color:#ffffff!important;font-weight:600!important;}
div[data-baseweb="select"], div[data-baseweb="select"]>div {background:#ffffff!important;color:#1a1a1a!important;border:2px solid #005a9e!important;border-radius:8px!important;font-weight:600!important;}
.stButton>button {background:#0078d7!important;color:white!important;border-radius:6px!important;font-weight:600!important;border:none!important;}
.stButton>button:hover {background:#005a9e!important;transform:scale(1.03);}
.weather-box {background:#f8fbff!important;border:2px solid #0078d7!important;border-radius:8px!important;padding:10px!important;font-weight:600!important;}
[data-testid="stChatInput"] textarea {background:#ffffff!important;border:2px solid #0078d7!important;border-radius:8px!important;color:#1a1a1a!important;}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align:center;'>🌊 FloodGuard AI – InnovateX Hackathon 2025</h1>", unsafe_allow_html=True)
st.caption("💻 Team Project | XGBoost ML | Gemini 1.5 Flash | Voice Alerts | SDG 13 & 17")

# ---------- SESSION ----------
for key in ["risk", "ai_summary", "audio", "messages"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["ai_summary", "audio", "messages"] else "N/A"

# ---------- LOAD MODEL ----------
@st.cache_resource
def load_model():
    try:
        model = joblib.load("model/flood_model.pkl")
        st.success("✅ ML Model Loaded (XGBoost)")
        return model
    except:
        st.warning("⚠️ Model not found — Using rule-based fallback.")
        return None

model = load_model()

# ---------- GEMINI ----------
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if key:
            genai.configure(api_key=key)
            gmodel = genai.GenerativeModel("gemini-1.5-flash")
            st.success("✅ Gemini 1.5 Flash Connected")
            return gmodel
    except Exception as e:
        st.warning(f"Gemini setup failed: {e}")
    return None

gemini = init_gemini()

# ---------- WEATHER API ----------
def get_weather(city="Dhaka", api_key=None):
    if not api_key:
        return 25.9, 83, 0
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=5).json()
        if r.get("cod") == 200:
            return r["main"]["temp"], r["main"]["humidity"], r.get("rain", {}).get("1h", 0)
    except:
        pass
    return 25.9, 83, 0

# ---------- SIDEBAR ----------
st.sidebar.header("📥 Flood Risk Inputs")
ow_key = st.sidebar.text_input("OpenWeather API Key", type="password", help="Optional for live weather data")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
loc = st.sidebar.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])

# ---------- FLOOD PREDICT ----------
def predict_flood(features):
    if model:
        df = pd.DataFrame([features], columns=["rainfall", "humidity", "temperature", "river_level", "pressure"])
        prob = model.predict_proba(df)[0][1]*100
        return ("High" if prob > 70 else "Medium" if prob > 30 else "Low"), prob
    s = (features[0]/100)+(features[3]/8)+(features[1]/100)-(features[2]/40)
    return ("High" if s > 2 else "Medium" if s > 1 else "Low"), 50

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    temp_w, hum_w, rain_w = get_weather(loc, ow_key) if ow_key else (temp, hum, rain)
    st.sidebar.info(f"Live Data: 🌡️ {temp_w}°C | 💧 {hum_w}% | 🌧️ {rain_w}mm")
    risk, prob = predict_flood([rain_w, hum_w, temp_w, level, 1013.25])
    st.session_state.risk = f"{risk} ({prob:.1f}%)"
    st.success(f"📍 {loc} — Flood Risk: {st.session_state.risk}")

    if gemini:
        try:
            prompt = f"Flood risk {risk} for {loc}. Rain {rain}mm, Temp {temp}°C, Hum {hum}%, Level {level}m. Give 2 short Bangla+English safety tips."
            res = gemini.generate_content(prompt)
            txt = res.text.strip()
            st.session_state.ai_summary = txt
            tts_text = txt.split("\n")[0][:100]
            tts = gTTS(tts_text, lang="bn")
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            st.session_state.audio = buf.getvalue()
        except Exception as e:
            st.session_state.ai_summary = f"AI Error: {e}"

# ---------- MAIN CONTENT ----------
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("☁️ Daily Weather & Rainfall Report")
    t, h, r = get_weather(loc, ow_key)
    st.markdown(f"<div class='weather-box'>🌤️ Haze | 🌡️ {t}°C | 💧 {h}% | 🌧️ {r}mm/h | 💨 0m/s</div>", unsafe_allow_html=True)

with col2:
    if st.session_state.ai_summary:
        st.info(st.session_state.ai_summary)
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3")

# ---------- RIVER STATUS ----------
st.subheader("🌊 River Status Board (Live Simulation)")
rivers = [
    {"River": "Padma", "Station": "Goalundo", "Level": 8.7, "Danger": 10.5},
    {"River": "Jamuna", "Station": "Sirajganj", "Level": 9.3, "Danger": 11.0},
    {"River": "Meghna", "Station": "Ashugonj", "Level": 7.8, "Danger": 9.2},
]
df_river = pd.DataFrame(rivers)
df_river["Risk"] = np.where(df_river["Level"] > df_river["Danger"], "High",
                    np.where(df_river["Level"] > df_river["Danger"] * 0.9, "Medium", "Low"))
st.dataframe(df_river, use_container_width=True, hide_index=True)

# ---------- MAP ----------
st.subheader("🗺️ Flood Risk Heatmap (Dhaka Focus)")
m = folium.Map(location=[23.81,90.41], zoom_start=9, tiles="CartoDB Positron")
heat_points = [[23.8103,90.4125,0.5],[23.723,90.408,0.8],[23.867,90.384,0.4],[23.780,90.420,0.6],[23.850,90.450,0.7]]
HeatMap(heat_points, radius=18, blur=12, min_opacity=0.3).add_to(m)
st_folium(m, width=1000, height=500)

# ---------- TREND ----------
st.subheader("📊 30-Day Rainfall & Flood Risk Trend")
dates = pd.date_range(datetime.now()-timedelta(days=29), periods=30)
rain_vals = np.clip(50+30*np.sin(np.linspace(0,3,30))+np.random.normal(0,10,30),0,200)
risk_vals = ["Low" if rv<60 else "Medium" if rv<120 else "High" for rv in rain_vals]
df = pd.DataFrame({"Date":dates,"Rainfall (mm)":rain_vals,"Risk":risk_vals})
fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
              color_discrete_map={"Low":"#43a047","Medium":"#fb8c00","High":"#e53935"},
              title="Rainfall vs Flood Risk Trend")
st.plotly_chart(fig, use_container_width=True)

# ---------- FOOTER ----------
st.divider()
st.markdown("<p style='text-align:center;font-weight:600;'>🌊 FloodGuard AI © 2025 | InnovateX Hackathon | Team Project 💻</p>", unsafe_allow_html=True)
