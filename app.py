import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import requests

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- THEME ----------
st.markdown("""
<style>
.stApp {background-color:#e3f2fd !important;color:#0d1b2a;font-family:"Inter",sans-serif;}
[data-testid="stSidebar"] {background-color:#bbdefb!important;border-right:2px solid #64b5f6!important;}
[data-testid="stSidebar"] * {color:#0d1b2a!important;}
div[data-baseweb="select"] > div {background-color:#ffffff!important;color:#0d1b2a!important;border-radius:6px!important;}
.stButton>button{background-color:#1565c0!important;color:white!important;border-radius:8px;font-weight:600;}
.stButton>button:hover{background-color:#0d47a1!important;}
@media (max-width:768px){.stApp{font-size:15px!important;}.stButton>button{width:100%!important;}}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Final 2026")
st.caption("💻 Zahid Hasan | Gemini 2.5 Flash + Smart Dashboard + Weather Report")

# ---------- SESSION STATE ----------
if "risk" not in st.session_state: st.session_state.risk = "N/A"
if "ai_summary" not in st.session_state: st.session_state.ai_summary = None
if "audio" not in st.session_state: st.session_state.audio = None
if "messages" not in st.session_state: st.session_state.messages = []

# ---------- GEMINI INIT ----------
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.warning("⚠️ Gemini API Key missing — demo mode")
            return None
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        st.success("✅ Gemini 2.5 Flash Connected")
        return model
    except Exception as e:
        st.error(f"Gemini setup failed → {e}")
        return None

gemini = init_gemini()

# ---------- SIMPLE MODEL ----------
def predict_flood(r, t, h, l):
    score = (r/100) + (l/8) + (h/100) - (t/40)
    return "High" if score > 2 else "Medium" if score > 1 else "Low"

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("📥 Flood Risk Inputs")
    rain = st.slider("🌧️ Rainfall (mm)", 0, 500, 100)
    temp = st.slider("🌡️ Temperature (°C)", 10, 40, 28)
    hum = st.slider("💧 Humidity (%)", 30, 100, 85)
    level = st.slider("🌊 River Level (m)", 0.0, 20.0, 6.0)
    loc = st.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])
    if st.button("🔮 Predict Flood Risk", use_container_width=True):
        st.session_state.risk = predict_flood(rain, temp, hum, level)
        if gemini:
            try:
                prompt = f"Flood forecast for {loc}: Rain {rain}mm, River {level}m, Humidity {hum}%, Temp {temp}°C. Risk = {st.session_state.risk}. Give 2 Bangla safety tips with English translation."
                res = gemini.generate_content(prompt)
                st.session_state.ai_summary = res.text
                short = res.text.split("\n")[0][:100]
                tts = gTTS(short, lang="bn")
                buf = BytesIO()
                tts.write_to_fp(buf)
                st.session_state.audio = buf.getvalue()
            except Exception as e:
                st.session_state.ai_summary = f"AI Error: {e}"

# ---------- FORECAST ----------
st.subheader(f"📍 {loc} Flood Forecast")
color = {"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"}.get(st.session_state.risk,"#000")
if st.session_state.risk == "N/A":
    st.info("👉 Use sidebar to predict flood risk.")
else:
    st.markdown(f"<h3 style='color:{color};text-align:center;'>🌀 {st.session_state.risk} Flood Risk</h3>", unsafe_allow_html=True)
    if st.session_state.risk == "High":
        st.error("🚨 HIGH RISK! Move to higher ground immediately.")
    elif st.session_state.risk == "Medium":
        st.warning("⚠️ Moderate risk — Stay alert.")
    else:
        st.success("✅ Low risk — Safe conditions.")

if st.session_state.ai_summary:
    st.markdown("### 📋 Safety Tips")
    st.write(st.session_state.ai_summary)
if st.session_state.audio:
    st.audio(st.session_state.audio, format="audio/mp3")

# ---------- DAILY WEATHER REPORT ----------
st.subheader("☁️ Daily Weather & Rainfall Report (OpenWeather API)")
try:
    api_key = st.secrets.get("OPENWEATHER_KEY", None)
    if api_key:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={loc}&appid={api_key}&units=metric"
        data = requests.get(url).json()
        temp_now = data['main']['temp']
        hum_now = data['main']['humidity']
        desc = data['weather'][0]['description'].title()
        rain_mm = data.get('rain', {}).get('1h', 0)
        st.success(f"🌤️ **{desc}**, 🌡️ {temp_now}°C, 💧 {hum_now}%, 🌧️ {rain_mm}mm (1h)")
    else:
        st.info("⚙️ OpenWeather API not set — showing simulated data.")
        st.text("🌤️ Condition: Cloudy | 🌡️ Temp: 29°C | 💧 Humidity: 84% | 🌧️ Rain: 3mm/h")
except Exception as e:
    st.warning(f"Weather API error: {e}")

# ---------- DASHBOARD ----------
st.subheader("📊 30-Day Rainfall & Flood Risk Trend")
dates = pd.date_range(datetime.now() - timedelta(days=29), periods=30)
rain_data = np.clip(50 + 30*np.sin(np.linspace(0,3,30)) + np.random.normal(0,10,30), 0, 200)
risk_data = ["Low" if r<60 else "Medium" if r<120 else "High" for r in rain_data]
df = pd.DataFrame({"Date":dates,"Rainfall (mm)":rain_data,"Risk":risk_data})
fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
              color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
              title="Rainfall vs Flood Risk Trend (Simulated)")
st.plotly_chart(fig, use_container_width=True)

# ---------- CHATBOT ----------
st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
if q := st.chat_input("Ask a question / প্রশ্ন করুন..."):
    st.session_state.messages.append({"role":"user","content":q})
    with st.chat_message("user"): st.markdown(q)
    with st.chat_message("assistant"):
        if gemini:
            try:
                prompt = f"You are FloodGuard AI (Bangladesh flood expert). Reply short in Bangla + English: {q}"
                reply = gemini.generate_content(prompt).text
            except Exception as e:
                reply = f"AI error: {e}"
        else:
            reply = "Demo mode – Gemini API key missing."
        st.markdown(reply)
        st.session_state.messages.append({"role":"assistant","content":reply})
if st.button("🗑️ Clear Chat"): st.session_state.messages = []; st.rerun()

# ---------- FOOTER ----------
st.divider()
st.markdown("""
🌊 **FloodGuard AI © 2026** | Developed by **Zahid Hasan** 💻  
🔗 [GitHub Repository](https://github.com/zahid397/FloodGuard-AI)
""", unsafe_allow_html=True)
