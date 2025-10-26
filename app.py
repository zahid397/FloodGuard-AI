import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import requests
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
/* 🌊 Base app background */
.stApp {
    background-color: #eaf4fc !important;
    color: #0a192f !important;
    font-family: 'Inter', sans-serif;
}

/* 📚 Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #dbeafe 0%, #e3f2fd 100%) !important;
    border-right: 2px solid #64b5f6 !important;
}
[data-testid="stSidebar"] * {
    color: #0a192f !important;
}

/* 🧭 Input controls: dropdown / slider */
div[data-baseweb="select"] {
    background: #ffffff !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;
    padding: 6px !important;
}
div[data-baseweb="select"]:hover {
    box-shadow: 0 0 0 2px #64b5f6 inset !important;
}

/* 🌤️ Weather info box */
.weather-box {
    background: linear-gradient(135deg, #f8fdff 0%, #e6f4ff 100%);
    border-radius: 12px;
    border: 1px solid rgba(13,71,161,0.15);
    padding: 14px 16px;
    margin-bottom: 10px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.08);
    font-weight: 600;
}

/* ✅ Gemini connect box */
.success-box {
    background: #ffffff;
    border-left: 6px solid #43a047;
    color: #1b5e20;
    font-weight: 600;
    border-radius: 6px;
    padding: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
}

/* 💬 Chat bubble style */
[data-testid="stChatMessage"] {
    background: #f0f9ff;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 5px;
}
[data-testid="stChatMessage"] p {
    color: #0a192f !important;
    font-weight: 500;
}

/* 🎹 Buttons */
.stButton>button {
    background-color: #1565c0 !important;
    color: white !important;
    border-radius: 8px;
    font-weight: 600;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.stButton>button:hover {
    background-color: #0d47a1 !important;
}

/* 📊 Plot clean background */
.js-plotly-plot .plotly {
    background: #fdfdfd !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<h1 style='text-align:center;color:#0a192f;font-weight:800;margin-bottom:8px;'>
🌊 FloodGuard AI – Hackathon Pro Final 2026
</h1>
<p style='text-align:center;font-size:17px;color:#08336e;font-weight:700;
text-shadow:0 0 6px rgba(255,255,255,0.9);
background:rgba(187,222,251,0.5);border-radius:8px;padding:6px 10px;
display:inline-block;'>
💻 Zahid Hasan | Gemini 2.5 Flash ⚡ | Smart Dashboard 📊 | Weather ☁️ | River Board 🌊
</p>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
for k in ["risk","ai_summary","audio","messages","loc"]:
    if k not in st.session_state:
        st.session_state[k] = "N/A" if k=="risk" else None if k in ["ai_summary","audio","loc"] else []

# ---------- GEMINI ----------
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if not key:
            return None
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        st.markdown("<div class='success-box'>✅ Gemini 2.5 Flash Connected</div>", unsafe_allow_html=True)
        return model
    except Exception as e:
        st.warning(f"Gemini setup failed → {e}")
        return None

gemini = init_gemini()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("📥 Flood Risk Inputs")
    rain = st.slider("🌧️ Rainfall (mm)", 0, 500, 100)
    temp = st.slider("🌡️ Temperature (°C)", 10, 40, 28)
    hum = st.slider("💧 Humidity (%)", 30, 100, 85)
    level = st.slider("🌊 River Level (m)", 0.0, 20.0, 6.0)
    loc = st.selectbox("📍 Location", ["Dhaka","Sylhet","Rajshahi","Chittagong"])
    st.session_state.loc = loc
    if st.button("🔮 Predict Flood Risk", use_container_width=True):
        st.session_state.risk = "High" if (rain+level+hum-temp)>250 else "Medium" if (rain+level)>150 else "Low"
        if gemini:
            prompt = f"{loc} flood forecast. Rain={rain}, River={level}, Hum={hum}, Temp={temp}. Give 2 Bangla safety tips."
            res = gemini.generate_content(prompt)
            st.session_state.ai_summary = res.text
            tts = gTTS(res.text.split("\n")[0][:100], lang="bn")
            buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
            st.session_state.audio = buf.getvalue()

# ---------- WEATHER ----------
st.subheader("☁️ Daily Weather & Rainfall Report (OpenWeather)")
try:
    key = st.secrets.get("OPENWEATHER_KEY")
    loc = st.session_state.get("loc","Dhaka")
    if key:
        res = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={loc}&appid={key}&units=metric"
        ).json()
        desc = res["weather"][0]["description"].title()
        tempn = res["main"]["temp"]; hum = res["main"]["humidity"]
        rain_mm = res.get("rain",{}).get("1h",0); wind = res["wind"]["speed"]
        st.markdown(
            f"<div class='weather-box'>🌤️ {desc} | 🌡️ {tempn}°C | 💧 {hum}% | 🌧️ {rain_mm}mm/h | 💨 {wind}m/s</div>",
            unsafe_allow_html=True
        )
except:
    st.info("⚙️ Weather API updating...")

# ---------- RIVER BOARD ----------
st.subheader("🌊 River Status Board (Live Simulation)")
rivers=[
    {"River":"Padma","Station":"Goalundo","Level (m)":8.7,"Danger (m)":10.5,"Risk":"Low"},
    {"River":"Jamuna","Station":"Sirajganj","Level (m)":9.3,"Danger (m)":11.0,"Risk":"Low"},
    {"River":"Meghna","Station":"Ashuganj","Level (m)":7.8,"Danger (m)":9.2,"Risk":"Low"},
]
st.dataframe(pd.DataFrame(rivers), use_container_width=True, hide_index=True)

# ---------- TREND ----------
st.subheader("📊 30-Day Rainfall & Flood Risk Trend")
dates = pd.date_range(datetime.now()-timedelta(days=29), periods=30)
rain = np.clip(50+30*np.sin(np.linspace(0,3,30))+np.random.normal(0,10,30),0,200)
risk = ["Low" if r<60 else "Medium" if r<120 else "High" for r in rain]
df = pd.DataFrame({"Date":dates,"Rainfall (mm)":rain,"Risk":risk})
fig = px.line(df,x="Date",y="Rainfall (mm)",color="Risk",
    color_discrete_map={"Low":"#43a047","Medium":"#fb8c00","High":"#e53935"},
    title="Rainfall vs Flood Risk Trend")
st.plotly_chart(fig,use_container_width=True)

# ---------- CHATBOT ----------
st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if q := st.chat_input("Ask a question / প্রশ্ন করুন..."):
    st.session_state.messages.append({"role":"user","content":q})
    with st.chat_message("user"): st.markdown(q)
    with st.chat_message("assistant"):
        if gemini:
            reply = gemini.generate_content(f"Bangladesh flood expert reply in Bangla+English: {q}").text
            st.markdown(reply)
            try:
                tts = gTTS(reply.split("\n")[0][:100], lang="bn")
                buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
                st.audio(buf, format="audio/mp3")
            except: pass
        else:
            st.warning("Demo mode — Gemini API key missing.")
        st.session_state.messages.append({"role":"assistant","content":reply})

if st.button("🗑️ Clear Chat"): st.session_state.messages=[]; st.rerun()

# ---------- FOOTER ----------
st.divider()
st.markdown("""
🌊 **FloodGuard AI © 2026** | Developed by **Zahid Hasan** 💻  
🔗 [GitHub Repository](https://github.com/zahid397/FloodGuard-AI)
""", unsafe_allow_html=True)
