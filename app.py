import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# ---- PAGE CONFIG ----
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---- MS WORD CLEAN THEME ----
st.markdown("""
<style>
.stApp {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    font-family: "Segoe UI", sans-serif !important;
}
* { opacity: 1 !important; }

/* Sidebar clean blue */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0078d7,#0099ff) !important;
    border-right: 3px solid #005a9e !important;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Location select clean white */
div[data-baseweb="select"], div[data-baseweb="select"] > div {
    background: #ffffff !important;
    color: #1a1a1a !important;
    border: 2px solid #e0e0e0 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* Buttons */
.stButton > button {
    background: #0078d7 !important;
    color: white !important;
    border-radius: 6px !important;
    border: none !important;
    font-weight: 600 !important;
}
.stButton > button:hover {
    background: #005a9e !important;
    transform: scale(1.03);
}

/* Weather box */
.weather-box {
    background: #f8fbff !important;
    border: 2px solid #0078d7 !important;
    border-radius: 8px !important;
    padding: 10px !important;
    font-weight: 600 !important;
    color: #1a1a1a !important;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    border: 2px solid #0078d7 !important;
    color: #1a1a1a !important;
    border-radius: 8px !important;
}

/* Headers */
h1,h2,h3,h4,h5,h6,.stCaption,footer {
    color: #1a1a1a !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

# ---- HEADER ----
st.markdown("<h1 style='text-align:center;'>🌊 FloodGuard AI – Hackathon Final 2026</h1>", unsafe_allow_html=True)
st.caption("💻 Zahid Hasan | Gemini 2.5 Flash | Smart Dashboard | Voice Chatbot")

# ---- SESSION STATE ----
for key in ["risk", "ai_summary", "audio", "messages"]:
    if key not in st.session_state:
        st.session_state[key] = "N/A" if key == "risk" else None if key in ["ai_summary", "audio"] else []

# ---- GEMINI ----
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

# ---- SIDEBAR INPUT ----
st.sidebar.header("📥 Flood Risk Inputs")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
loc = st.sidebar.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])

# ---- SIMPLE PREDICTION ----
def predict(r, t, h, l):
    s = (r / 100) + (l / 8) + (h / 100) - (t / 40)
    return "High" if s > 2 else "Medium" if s > 1 else "Low"

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    risk_level = predict(rain, temp, hum, level)
    st.session_state.risk = risk_level
    st.success(f"Predicted Flood Risk for {loc}: **{risk_level}**")

    if gemini:
        try:
            res = gemini.generate_content(
                f"Flood risk for {loc}. Rain {rain}mm, Temp {temp}°C, Hum {hum}%, Level {level}m. Give 2 short Bangla+English safety tips."
            )
            txt = res.text
            st.session_state.ai_summary = txt
            st.markdown(f"### 🌧️ AI Tips:\n{txt}")
            tts = gTTS(txt.split('\n')[0][:100], lang="bn")
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            st.audio(buf, format="audio/mp3")
        except Exception as e:
            st.error(f"AI unavailable: {e}")

# ---- MAIN DASHBOARD ----
st.subheader("☁️ Daily Weather & Rainfall Report (OpenWeather)")
st.markdown("<div class='weather-box'>🌤️ Haze | 🌡️ 25.9°C | 💧 83% | 🌧️ 0mm/h | 💨 0m/s</div>", unsafe_allow_html=True)

st.subheader("🌊 River Status Board (Live Simulation)")
rivers = [
    {"River": "Padma", "Station": "Goalundo", "Level": 8.7, "Danger": 10.5},
    {"River": "Jamuna", "Station": "Sirajganj", "Level": 9.3, "Danger": 11.0},
    {"River": "Meghna", "Station": "Ashuganj", "Level": 7.8, "Danger": 9.2},
]
df = pd.DataFrame(rivers)
df["Risk"] = np.where(df["Level"] > df["Danger"], "High",
             np.where(df["Level"] > df["Danger"] * 0.9, "Medium", "Low"))
st.dataframe(df, use_container_width=True, hide_index=True)

st.subheader("📊 30-Day Rainfall & Flood Risk Trend")
dates = pd.date_range(datetime.now() - timedelta(days=29), periods=30)
rain_vals = np.clip(50 + 30 * np.sin(np.linspace(0, 3, 30)) + np.random.normal(0, 10, 30), 0, 200)
risk = ["Low" if r < 60 else "Medium" if r < 120 else "High" for r in rain_vals]
df2 = pd.DataFrame({"Date": dates, "Rainfall (mm)": rain_vals, "Risk": risk})
fig = px.line(df2, x="Date", y="Rainfall (mm)", color="Risk",
              color_discrete_map={"Low": "#43a047", "Medium": "#fb8c00", "High": "#e53935"},
              title="Rainfall vs Flood Risk Trend")
st.plotly_chart(fig, use_container_width=True)

# ---- CHATBOT ----
st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if q := st.chat_input("Ask a question / প্রশ্ন করুন..."):
    st.session_state.messages.append({"role": "user", "content": q})
    with st.chat_message("assistant"):
        if gemini:
            reply = gemini.generate_content(f"FloodGuard AI reply in Bangla+English: {q}").text
            st.markdown(reply)
            tts = gTTS(reply.split('\n')[0][:100], lang="bn")
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            st.audio(buf, format="audio/mp3")
        else:
            reply = "Demo mode — Gemini API key missing."
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

st.divider()
st.markdown("<p style='text-align:center;font-weight:600;'>🌊 FloodGuard AI © 2026 | Developed by Zahid Hasan 💻</p>", unsafe_allow_html=True)
