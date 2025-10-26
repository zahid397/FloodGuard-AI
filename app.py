import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# --- FIX ALL FADING / TRANSPARENCY ---
st.markdown("""
<style>
.stApp {
    background: #dff3ff !important;
    color: #001b33 !important;
    font-family: 'Inter', sans-serif;
}

/* Make all text solid (no transparency) */
* {
    opacity: 1.0 !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0078d4, #0099ff) !important;
    border-right: 3px solid #005fa3 !important;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Clean white selectbox */
div[data-baseweb="select"], div[data-baseweb="select"] > div {
    background: #ffffff !important;
    color: #001b33 !important;
    border-radius: 10px !important;
    border: 2px solid #ffffff !important;
    font-weight: 600 !important;
}

/* Buttons */
.stButton > button {
    background: #0078d4 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button:hover {
    background: #005fa3 !important;
    transform: scale(1.03);
}

/* Weather + card box */
.weather-box {
    background: white !important;
    border: 2px solid #90e0ff !important;
    border-radius: 10px !important;
    padding: 10px;
    color: #001b33 !important;
    font-weight: 600 !important;
}

/* Chat styling */
[data-testid="stChatInput"] textarea {
    background: white !important;
    color: #001b33 !important;
    border: 1px solid #0078d4 !important;
    border-radius: 10px !important;
}
[data-testid="stChatMessage"] {
    background: #e8f6ff !important;
    border-radius: 10px !important;
    padding: 10px !important;
    margin-bottom: 5px !important;
}

/* Footer visible */
footer, .stCaption, .stText, .stMarkdown, .stSuccess, h1, h2, h3, h4 {
    color: #001b33 !important;
    opacity: 1.0 !important;
}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1 style='text-align:center;'>🌊 FloodGuard AI – Hackathon Final 2026</h1>", unsafe_allow_html=True)
st.caption("💻 Zahid Hasan | Gemini 2.5 Flash | Smart Dashboard | Voice Chatbot")

# --- SESSION STATE ---
for k in ["risk", "ai_summary", "audio", "messages"]:
    if k not in st.session_state:
        st.session_state[k] = "N/A" if k == "risk" else None if k in ["ai_summary", "audio"] else []

# --- GEMINI SETUP ---
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            st.success("✅ Gemini 2.5 Flash Connected")
            return model
    except Exception as e:
        st.warning(f"Gemini setup failed: {e}")
    return None

gemini = init_gemini()

# --- SIDEBAR ---
st.sidebar.header("📥 Flood Risk Inputs")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
loc = st.sidebar.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])

def predict(r, t, h, l):
    s = (r/100) + (l/8) + (h/100) - (t/40)
    return "High" if s > 2 else "Medium" if s > 1 else "Low"

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    st.session_state.risk = predict(rain, temp, hum, level)
    if gemini:
        res = gemini.generate_content(f"Flood risk for {loc}. Rain {rain}mm, Temp {temp}°C, Hum {hum}%, Level {level}m. Give 2 Bangla+English safety tips.")
        txt = res.text
        st.session_state.ai_summary = txt
        tts = gTTS(txt.split("\\n")[0][:100], lang="bn")
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        st.session_state.audio = buf.getvalue()

# --- WEATHER SECTION ---
st.subheader("☁️ Daily Weather & Rainfall Report (OpenWeather)")
st.markdown("<div class='weather-box'>🌤️ Haze | 🌡️ 25.9°C | 💧 83% | 🌧️ 0mm/h | 💨 0m/s</div>", unsafe_allow_html=True)

# --- RIVER STATUS ---
st.subheader("🌊 River Status Board (Live Simulation)")
rivers = [
    {"River":"Padma","Station":"Goalundo","Level":8.7,"Danger":10.5},
    {"River":"Jamuna","Station":"Sirajganj","Level":9.3,"Danger":11.0},
    {"River":"Meghna","Station":"Ashuganj","Level":7.8,"Danger":9.2},
]
df = pd.DataFrame(rivers)
df["Risk"] = np.where(df["Level"]>df["Danger"],"High",np.where(df["Level"]>df["Danger"]*0.9,"Medium","Low"))
st.dataframe(df,use_container_width=True,hide_index=True)

# --- RAINFALL TREND ---
st.subheader("📊 30-Day Rainfall & Flood Risk Trend")
dates = pd.date_range(datetime.now() - timedelta(days=29), periods=30)
rain_vals = np.clip(50 + 30*np.sin(np.linspace(0,3,30)) + np.random.normal(0,10,30), 0, 200)
risk = ["Low" if r < 60 else "Medium" if r < 120 else "High" for r in rain_vals]
df2 = pd.DataFrame({"Date":dates,"Rainfall (mm)":rain_vals,"Risk":risk})
fig = px.line(df2, x="Date", y="Rainfall (mm)", color="Risk",
    color_discrete_map={"Low":"#43a047","Medium":"#fb8c00","High":"#e53935"},
    title="Rainfall vs Flood Risk Trend")
st.plotly_chart(fig,use_container_width=True)

# --- CHATBOT ---
st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if q := st.chat_input("Ask a question / প্রশ্ন করুন..."):
    st.session_state.messages.append({"role":"user","content":q})
    with st.chat_message("assistant"):
        if gemini:
            reply = gemini.generate_content(f"FloodGuard AI reply in Bangla+English: {q}").text
            st.markdown(reply)
            tts = gTTS(reply.split("\\n")[0][:120], lang="bn")
            buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
            st.audio(buf, format="audio/mp3")
        else:
            reply = "Demo mode — Gemini API key missing."
            st.markdown(reply)
        st.session_state.messages.append({"role":"assistant","content":reply})

if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# --- FOOTER ---
st.divider()
st.markdown("<p style='text-align:center;font-weight:600;'>🌊 FloodGuard AI © 2026 | Developed by Zahid Hasan 💻</p>", unsafe_allow_html=True)
