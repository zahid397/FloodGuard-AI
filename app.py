import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import joblib
import requests
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------------- STYLES ----------------
st.markdown("""
<style>
.stApp{background:#fff!important;color:#0a192f!important;font-family:"Segoe UI",sans-serif!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0078d7,#0099ff)!important;border-right:3px solid #005a9e!important;}
[data-testid="stSidebar"] *{color:#fff!important;font-weight:600!important;}
div[role="combobox"]{background:#ffffff!important;border:2px solid #005a9e!important;border-radius:10px!important;padding:5px 10px!important;}
.stButton>button{background:#0078d7!important;color:#fff!important;border:none!important;border-radius:8px!important;font-weight:700!important;}
.stButton>button:hover{background:#005a9e!important;transform:scale(1.03);}
.weather-box{background:#f8fbff!important;border:2px solid #0078d7!important;border-radius:10px!important;padding:10px!important;font-weight:600!important;}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;'>🌊 FloodGuard AI – InnovateX Hackathon 2025</h1>", unsafe_allow_html=True)
st.caption("💻 XGBoost ML | Gemini 2.5 Flash | Voice Tips | Team Project")

# ---------------- SESSION STATE ----------------
defaults = {
    "risk": "N/A",
    "ai_summary": None,
    "audio": None,
    "weather_data": {"temp": 25.9, "hum": 83, "rain": 0},
    "prediction_inputs": None,
    "chat_messages": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- LOAD MODEL ----------------
@st.cache_resource
def load_model():
    try:
        return joblib.load("model/flood_model.pkl")
    except Exception as e:
        # silently fallback
        return None

model = load_model()

# ---------------- GEMINI SETUP ----------------
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
        st.warning("⚠️ Gemini API key missing.")
        return None
    try:
        genai.configure(api_key=key)
        gmodel = genai.GenerativeModel("gemini-2.5-flash")
        st.success("✅ Gemini Connected (gemini-2.5-flash)")
        return gmodel
    except Exception as e:
        st.error(f"Gemini init failed: {e}")
        return None

gemini = init_gemini()

# ---------------- WEATHER FUNCTION ----------------
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

# ---------------- PREDICTION FUNCTION ----------------
def predict_flood(features):
    if model:
        try:
            df = pd.DataFrame([features], columns=["rainfall", "humidity", "temperature", "river_level", "pressure"])
            prob = model.predict_proba(df)[0][1] * 100
            risk = "High" if prob > 70 else "Medium" if prob > 30 else "Low"
            return f"{risk} ({prob:.1f}%)"
        except Exception as e:
            st.error(f"Model prediction error: {e}")
    # fallback logic
    s = (features[0]/100) + (features[3]/8) + (features[1]/100) - (features[2]/40)
    risk = "High" if s > 2 else "Medium" if s > 1 else "Low"
    return f"{risk} (Rule-Based)"

# ---------------- PDF REPORT FUNCTION ----------------
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
def create_pdf(risk, weather, summary, inputs):
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
    if summary:
        y = 590
        for line in summary[:600].split("\n"):
            c.drawString(60, y, line)
            y -= 15
    c.save()
    buf.seek(0)
    return buf

# ---------------- SIDEBAR ----------------
st.sidebar.header("📥 Flood Risk Inputs")
ow_key = st.sidebar.text_input("OpenWeather API Key (Optional)", type="password")
loc = st.sidebar.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])
st.sidebar.divider()
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
pressure = st.sidebar.slider("💨 Pressure (hPa)", 950, 1050, 1013)

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    t, h, r = get_weather(loc, ow_key, {"temp": temp, "hum": hum, "rain": rain})
    st.session_state.weather_data = {"temp": t, "hum": h, "rain": r}
    st.session_state.prediction_inputs = {"rain": r, "hum": h, "temp": t, "level": level, "pressure": pressure, "loc": loc}
    st.session_state.risk = predict_flood([r, h, t, level, pressure])
    st.session_state.ai_summary = None
    st.session_state.audio = None

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["① Analysis", "② Weather", "③ AI Tips", "④ Chat Assistant", "⑤ About"])

with tab1:
    st.subheader("🔮 Flood Risk Analysis")
    if st.session_state.risk != "N/A":
        color_map = {"Low": "#43a047", "Medium": "#fb8c00", "High": "#e53935"}
        risk_level = st.session_state.risk.split()[0]
        color = color_map.get(risk_level, "#0a192f")
        st.markdown(f"<h3>📍 {loc} — Predicted Risk: <span style='color:{color};'>{st.session_state.risk}</span></h3>", unsafe_allow_html=True)
        dates = pd.date_range(datetime.now() - timedelta(days=29), periods=30)
        rain_vals = np.clip(50 + 30*np.sin(np.linspace(0,3,30)) + np.random.normal(0,10,30), 0, 200)
        risk_vals = ["Low" if rv<60 else "Medium" if rv<120 else "High" for rv in rain_vals]
        df_trend = pd.DataFrame({"Date": dates, "Rainfall (mm)": rain_vals, "Risk": risk_vals})
        fig = px.line(df_trend, x="Date", y="Rainfall (mm)", color="Risk",
                      color_discrete_map=color_map, title="Rainfall vs Flood Risk Trend (Simulation)")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)
        pdf_buf = create_pdf(st.session_state.risk, st.session_state.weather_data, st.session_state.ai_summary, st.session_state.prediction_inputs)
        st.download_button("📄 Download Flood Report", data=pdf_buf, file_name="FloodGuard_Report.pdf", mime="application/pdf")
    else:
        st.info("⬅️ Set inputs and click Predict Flood Risk")

with tab2:
    st.subheader("☁️ Weather")
    w = st.session_state.weather_data
    st.markdown(f"<div class='weather-box'>📍 {loc} | 🌡️ {w['temp']:.1f}°C | 💧 {w['hum']}% | 🌧️ {w['rain']}mm</div>", unsafe_allow_html=True)

with tab3:
    st.subheader("🤖 AI Safety Tips")
    st.markdown("**Model:** " + ("Connected" if gemini else "Not connected"))
    if st.button("⚡ Generate Tips", use_container_width=True):
        if not gemini:
            st.error("Gemini not configured.")
        elif st.session_state.risk == "N/A":
            st.info("Please predict flood risk first.")
        else:
            with st.spinner("Generating safety tips..."):
                try:
                    p = st.session_state.prediction_inputs
                    prompt = (f"Flood risk is {st.session_state.risk} for {p['loc']} "
                              f"(Rain: {p['rain']}mm, Level: {p['level']}m). Provide 2 Bangla tips then 2 English tips.")
                    res = gemini.generate_content(prompt)
                    txt = (res.text or "").strip()
                    st.session_state.ai_summary = txt
                    # generate Bangla voice
                    bangla_lines = [l for l in txt.split("\n") if any('\u0980' <= ch <= '\u09FF' for ch in l)]
                    if bangla_lines:
                        tts = gTTS("\n".join(bangla_lines[:2])[:150], lang="bn")
                        buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
                        st.session_state.audio = buf.getvalue()
                except Exception as e:
                    st.session_state.ai_summary = f"AI Error: {e}"
    if st.session_state.ai_summary:
        st.info(st.session_state.ai_summary)
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3")

with tab4:
    st.subheader("💬 Chat Assistant (Bangla + English)")
    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    q = st.chat_input("আপনার প্রশ্ন লিখুন / Ask anything…")
    if q:
        st.session_state.chat_messages.append({"role":"user","content":q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            if not gemini:
                reply = "⚠️ Gemini not configured."
            else:
                try:
                    prompt = (f"You are FloodGuard Assistant. Current risk={st.session_state.risk}. "
                              f"Reply Bangla then English: {q}")
                    res = gemini.generate_content(prompt)
                    reply = (res.text or "").strip()
                except Exception as e:
                    reply = f"AI Error: {e}"
            st.markdown(reply)
            st.session_state.chat_messages.append({"role":"assistant","content":reply})

with tab5:
    st.markdown("### 🌊 About FloodGuard AI")
    st.write("This is AI-powered flood prediction & advisory for Bangladesh. Developed for InnovateX Hackathon 2025.")

st.divider()
st.markdown("<p style='text-align:center;font-weight:600;'>🌊 FloodGuard AI © 2025 | Team Project 💻</p>", unsafe_allow_html=True)
