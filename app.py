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
from reportlab.lib.pagesizes import letter  # ✅ fixed import
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- THEME ----------
st.markdown("""
<style>
.stApp {background-color:#ffffff!important;color:#0a192f!important;font-family:"Segoe UI",sans-serif!important;}
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#0078d7,#0099ff)!important;
    border-right:3px solid #005a9e!important;
}
[data-testid="stSidebar"] * {color:#ffffff!important;font-weight:600!important;}
div[data-baseweb="select"], div[data-baseweb="select"]>div {
    background:#ffffff!important;
    color:#0a192f!important;
    border:2px solid #005a9e!important;
    border-radius:10px!important;
    box-shadow:0 3px 6px rgba(0,0,0,0.15)!important;
    padding:4px 8px!important;
    font-weight:600!important;
}
div[data-baseweb="select"]:hover {
    border-color:#004b8d!important;
    box-shadow:0 4px 8px rgba(0,0,0,0.25)!important;
}
.stButton>button {
    background:#0078d7!important;
    color:white!important;
    border-radius:8px!important;
    font-weight:600!important;
    border:none!important;
    padding:6px 12px!important;
}
.stButton>button:hover {background:#005a9e!important;transform:scale(1.03);}
.weather-box {background:#f8fbff!important;border:2px solid #0078d7!important;border-radius:8px!important;padding:10px!important;font-weight:600!important;}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align:center;'>🌊 FloodGuard AI – InnovateX Hackathon 2025</h1>", unsafe_allow_html=True)
st.caption("💻 Team Project | XGBoost ML | Gemini 2.5 Flash | Voice Chatbot | SDG 13 & 17")

# ---------- SESSION STATE ----------
defaults = {
    "risk": "N/A",
    "ai_summary": None,
    "audio": None,
    "weather_data": {"temp": 25.9, "hum": 83, "rain": 0},
    "prediction_inputs": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- LOAD MODEL ----------
@st.cache_resource
def load_model():
    try:
        model = joblib.load("model/flood_model.pkl")  # ✅ ensure correct path
        st.success("✅ ML Model Loaded (XGBoost)")
        return model
    except Exception:
        st.warning("⚠️ Model not found — Using rule-based fallback.")
        return None

model = load_model()

# ---------- GEMINI ----------
@st.cache_resource
def init_gemini():
    key = None
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not key:
        key = os.getenv("GEMINI_API_KEY")
    if not key:
        st.warning("⚠️ Gemini API Key not found. Please add one in Streamlit Secrets or environment.")
        return None
    try:
        genai.configure(api_key=key)
        try:
            gmodel = genai.GenerativeModel("gemini-1.5-flash")
        except Exception:
            gmodel = genai.GenerativeModel("gemini-pro")
        st.success("✅ Gemini Connected Successfully")
        return gmodel
    except Exception as e:
        st.error(f"Gemini setup failed: {e}")
        return None

gemini = init_gemini()

# ---------- WEATHER ----------
def get_weather(city, api_key, slider_data):
    if not api_key:
        return slider_data["temp"], slider_data["hum"], slider_data["rain"]
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=5).json()
        if r.get("cod") == 200:
            return r["main"]["temp"], r["main"]["humidity"], r.get("rain", {}).get("1h", 0)
    except Exception:
        pass
    return slider_data["temp"], slider_data["hum"], slider_data["rain"]

# ---------- PREDICTION ----------
def predict_flood(features):
    if model:
        try:
            df = pd.DataFrame([features], columns=["rainfall", "humidity", "temperature", "river_level", "pressure"])
            prob = model.predict_proba(df)[0][1] * 100
            risk = "High" if prob > 70 else "Medium" if prob > 30 else "Low"
            return f"{risk} ({prob:.1f}%)"
        except Exception as e:
            st.error(f"Model prediction error: {e}")
    s = (features[0]/100) + (features[3]/8) + (features[1]/100) - (features[2]/40)
    risk = "High" if s > 2 else "Medium" if s > 1 else "Low"
    return f"{risk} (Rule-Based)"

# ---------- PDF ----------
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

def create_pdf_report(risk, weather, summary, inputs):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("HeiseiMin-W3", 16)
    c.drawString(200, 750, "FloodGuard AI Report")
    c.setFont("HeiseiMin-W3", 12)
    c.drawString(50, 720, f"📍 Location: {inputs['loc']}")
    c.drawString(50, 700, f"Predicted Risk: {risk}")
    c.drawString(50, 680, f"Temperature: {weather['temp']:.1f}°C")
    c.drawString(50, 665, f"Humidity: {weather['hum']}%")
    c.drawString(50, 650, f"Rainfall: {weather['rain']} mm")
    c.drawString(50, 635, f"River Level: {inputs['level']} m")
    c.drawString(50, 620, f"Pressure: {inputs['pressure']} hPa")
    if summary and summary != "LOADING":
        c.setFont("HeiseiMin-W3", 11)
        y = 590
        for line in summary[:600].split("\n"):
            c.drawString(60, y, line)
            y -= 15
    c.save()
    buf.seek(0)
    return buf

# ---------- SIDEBAR ----------
st.sidebar.header("📥 Flood Risk Inputs")
ow_key = st.sidebar.text_input("OpenWeather API Key (Optional)", type="password")
loc = st.sidebar.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])

st.sidebar.divider()
st.sidebar.markdown("#### Manual Data Overrides")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
pressure = st.sidebar.slider("💨 Pressure (hPa)", 950, 1050, 1013)

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    temp_w, hum_w, rain_w = get_weather(loc, ow_key, {"temp": temp, "hum": hum, "rain": rain})
    st.session_state.weather_data = {"temp": temp_w, "hum": hum_w, "rain": rain_w}
    st.session_state.prediction_inputs = {"rain": rain_w, "hum": hum_w, "temp": temp_w, "level": level, "pressure": pressure, "loc": loc}
    st.session_state.risk = predict_flood([rain_w, hum_w, temp_w, level, pressure])
    st.session_state.ai_summary = "LOADING"
    st.session_state.audio = None
    st.rerun()

# ---------- MAIN ----------
st.subheader("🔮 Flood Risk Analysis")

if st.session_state.risk != "N/A":
    color = {"Low": "#43a047", "Medium": "#fb8c00", "High": "#e53935"}.get(st.session_state.risk.split()[0], "#0a192f")
    st.markdown(f"<h3>📍 {st.session_state.prediction_inputs['loc']} — Predicted Risk: <span style='color:{color};'>{st.session_state.risk}</span></h3>", unsafe_allow_html=True)

    # AI Analysis
    if st.session_state.ai_summary == "LOADING":
        with st.spinner("🤖 Gemini is analyzing flood situation..."):
            if gemini:
                try:
                    p = st.session_state.prediction_inputs
                    prompt = f"Flood risk is {st.session_state.risk} for {p['loc']} (Rain: {p['rain']}mm, Level: {p['level']}m). Provide 2 Bangla and 2 English short flood safety tips."
                    res = gemini.generate_content(prompt)
                    txt = res.text.strip()
                    st.session_state.ai_summary = txt
                    bangla_text = "\n".join(txt.split('\n')[:2])[:150]
                    tts = gTTS(bangla_text, lang="bn")
                    buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
                    st.session_state.audio = buf.getvalue()
                except Exception as e:
                    st.session_state.ai_summary = f"AI Error: {e}"
            else:
                st.session_state.ai_summary = "⚠️ Gemini not configured."

    if st.session_state.ai_summary and st.session_state.ai_summary != "LOADING":
        st.info(st.session_state.ai_summary)
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3")

    # ✅ PDF Download Option
    pdf_buffer = create_pdf_report(
        st.session_state.risk,
        st.session_state.weather_data,
        st.session_state.ai_summary,
        st.session_state.prediction_inputs
    )
    st.download_button("📄 Download Flood Report", data=pdf_buffer, file_name="FloodGuard_Report.pdf", mime="application/pdf")

    # ✅ Heatmap Section
    st.subheader("🗺️ Live Flood Risk Map (Bangladesh)")
    m = folium.Map(location=[23.8103, 90.4125], zoom_start=7)
    HeatMap([[23.81, 90.41, st.session_state.weather_data["rain"]/100]]).add_to(m)
    st_folium(m, width=700, height=450)

else:
    st.info("⬅️ Please set parameters in the sidebar and click 'Predict Flood Risk'")

# ---------- FOOTER ----------
st.divider()
st.markdown("<p style='text-align:center;font-weight:600;'>🌊 FloodGuard AI © 2025 | Gemini Flash | Team Project 💻</p>", unsafe_allow_html=True)
