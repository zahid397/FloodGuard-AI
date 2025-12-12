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
from reportlab.pdfbase.ttfonts import TTFont

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>  
div[data-testid="stChatMessage"] {  
    border-radius: 12px;  
    padding: 8px 12px;  
    margin: 5px 0;  
    max-width: 75%;  
}  
div[data-testid="stChatMessage"][data-role="user"] {  
    background-color: #0078d7;  
    color: white;  
    margin-left: auto;  
    margin-right: 5px;  
}  
div[data-testid="stChatMessage"][data-role="assistant"] {  
    background-color: #f1f1f1;  
    color: #0a192f;  
    margin-left: 5px;  
    margin-right: auto;  
}  
[data-testid="stChatInput"] textarea {  
    border-radius: 20px !important;  
    border: 2px solid #005a9e !important;  
}  
[data-testid="stChatInput"] button {  
    border-radius: 20px !important;  
    background-color: #0078d7 !important;  
    color: white !important;  
}  
</style>  """, unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;'>🌊 FloodGuard AI – InnovateX Hackathon 2025</h1>", unsafe_allow_html=True)
st.caption("💻 XGBoost ML | Gemini 2.5 Flash | Voice Tips | Team Project")

# ---------------- SESSION STATE ----------------
if 'risk' not in st.session_state:
    st.session_state.risk = "N/A"
if 'ai_summary' not in st.session_state:
    st.session_state.ai_summary = None
if 'audio' not in st.session_state:
    st.session_state.audio = None
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = {"temp": 25.9, "hum": 83, "rain": 0}
if 'prediction_inputs' not in st.session_state:
    st.session_state.prediction_inputs = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# ---------------- LOAD MODEL ----------------
@st.cache_resource
def load_model():
    try:
        return joblib.load("model/flood_model.pkl")
    except Exception:
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
        return None
        
    try:
        genai.configure(api_key=key)
        gmodel = genai.GenerativeModel("gemini-2.5-flash")
        return gmodel
    except Exception as e:
        st.error(f"Gemini init failed: {e}")
        return None

gemini = init_gemini()

# ---------------- 🔥 NEW: VOICE GENERATOR (Step 2) ----------------
def generate_bangla_voice(text):
    """
    Safely generates Bangla voice using gTTS, removing problematic characters.
    """
    try:
        # Filter out characters that might crash gTTS (surrogates)
        safe_text = "".join([c if ord(c) < 0xD800 else " " for c in text])
        if not safe_text.strip():
            return None
            
        tts = gTTS(safe_text[:200], lang="bn") # Limit to first 200 chars for speed
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        print(f"Voice Error: {e}")
        return None

# ---------------- 🔥 UPDATED: SMART AI RESPONSE (Step 1) ----------------
def smart_ai_response(user_msg, risk, location, gemini_model):
    """
    Handles Chat Logic: Panic Detection, Language Enforcement, Context.
    """
    if not gemini_model:
        return "⚠️ AI system offline. Please stay safe."

    # Detect Bangla
    is_bangla = any('\u0980' <= ch <= '\u09FF' for ch in user_msg)

    # Panic detection
    panic_words = ["help", "sos", "danger", "ভয়", "ডর", "বাঁচাও", "help me", "morlam", "mortesi", "bannya", "dube"]
    if any(w.lower() in user_msg.lower() for w in panic_words):
        return (
            "🚨 **জরুরী সতর্কতা!**\n\n"
            "দয়া করে শান্ত থাকুন।\n"
            "**৯৯৯** এ কল করুন।\n"
            "উঁচু বা নিরাপদ স্থানে যান।"
            if is_bangla else
            "🚨 **EMERGENCY ALERT!**\n\nCall **999** immediately.\nMove to safe higher ground."
        )

    # Language enforcement & System Prompt
    lang_instruction = "Answer in Bangla only." if is_bangla else "Answer in English only."

    system = f"""
    You are FloodGuard AI.
    Current Flood Risk: {risk}
    Location: {location}
    {lang_instruction}
    Keep answer under 3 sentences. Be helpful and calm.
    """

    try:
        res = gemini_model.generate_content(system + "\nUser Question: " + user_msg)
        text = (res.text or "").strip()
        return text
    except:
        return "⚠️ AI temporarily unavailable. Please follow local news."

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
        except Exception:
            pass
    # Fallback Rule-Based Logic
    s = (features[0]/100) + (features[3]/8) + (features[1]/100) - (features[2]/40)
    risk = "High" if s > 2 else "Medium" if s > 1 else "Low"
    return f"{risk} (Rule-Based)"

# ---------------- PDF REPORT FUNCTION ----------------
def create_pdf(risk, weather, summary, inputs):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, "FloodGuard AI Report")
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Location: {inputs['loc']}")
    c.drawString(50, 700, f"Predicted Risk: {risk}")
    c.drawString(50, 680, f"Temperature: {weather['temp']:.1f} C")
    c.drawString(50, 665, f"Humidity: {weather['hum']}%")
    c.drawString(50, 650, f"Rainfall: {weather['rain']} mm")
    
    # PDF Summary (Filtered for PDF safety)
    if summary:
        c.drawString(50, 605, "AI Analysis Summary:")
        # Only keep ASCII characters for PDF to prevent crash
        safe_summary = ''.join([i if ord(i) < 128 else ' ' for i in summary])
        text = c.beginText(50, 590)
        text.setFont("Helvetica", 10)
        lines = [safe_summary[i:i+80] for i in range(0, len(safe_summary), 80)]
        for line in lines[:15]:
            text.textLine(line)
        c.drawText(text)
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
        color_map = {"Low":"#43a047", "Medium":"#fb8c00", "High":"#e53935"}
        risk_level = st.session_state.risk.split()[0]
        color = color_map.get(risk_level, "#0a192f")
        st.markdown(f"<h3>📍 {loc} — Predicted Risk: <span style='color:{color};'>{st.session_state.risk}</span></h3>", unsafe_allow_html=True)
        
        dates = pd.date_range(datetime.now() - timedelta(days=29), periods=30)
        rain_vals = np.clip(50 + 30*np.sin(np.linspace(0,3,30)) + np.random.normal(0,10,30), 0, 200)
        risk_vals = ["Low" if rv<60 else "Medium" if rv<120 else "High" for rv in rain_vals]
        df = pd.DataFrame({"Date": dates, "Rainfall (mm)": rain_vals, "Risk": risk_vals})
        fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk", color_discrete_map=color_map)
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        pdf_buf = create_pdf(st.session_state.risk, st.session_state.weather_data, st.session_state.ai_summary, st.session_state.prediction_inputs)
        st.download_button("📄 Download Report", data=pdf_buf, file_name="Report.pdf", mime="application/pdf")
    else:
        st.info("⬅️ Please predict flood risk first.")

with tab2:
    w = st.session_state.weather_data
    st.markdown(f"<div style='padding:20px;background:#f0f2f6;border-radius:10px;text-align:center'><h3>{loc}</h3>🌡️ {w['temp']:.1f}°C | 💧 {w['hum']}% | 🌧️ {w['rain']}mm</div>", unsafe_allow_html=True)

with tab3:
    st.subheader("🤖 AI Safety Tips")
    if st.button("⚡ Generate Tips", use_container_width=True):
        if not gemini:
            st.error("Gemini Missing")
        elif st.session_state.risk == "N/A":
            st.info("Predict risk first.")
        else:
            with st.spinner("Generating AI Tips..."):
                try:
                    p = st.session_state.prediction_inputs
                    prompt = f"Risk is {st.session_state.risk} at {p['loc']}. Give 2 Bangla and 2 English short safety tips."
                    res = gemini.generate_content(prompt)
                    txt = res.text or ""
                    st.session_state.ai_summary = txt
                    
                    # 🔥 UPDATED: VOICE GENERATION LOGIC (Step 3)
                    bangla_lines = [l for l in txt.split("\n") if any('\u0980' <= ch <= '\u09FF' for ch in l)]
                    if bangla_lines:
                        audio_bytes = generate_bangla_voice(" ".join(bangla_lines[:2]))
                        st.session_state.audio = audio_bytes
                except Exception as e:
                    st.session_state.ai_summary = f"Error: {e}"
    
    if st.session_state.ai_summary: 
        st.info(st.session_state.ai_summary)
    if st.session_state.audio: 
        st.audio(st.session_state.audio, format="audio/mp3")

with tab4:
    st.subheader("💬 Smart Flood Assistant")
    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    
    q = st.chat_input("Ask about flood safety / বন্যা সম্পর্কে জানুন...")
    if q:
        st.session_state.chat_messages.append({"role":"user","content":q})
        with st.chat_message("user"):
            st.markdown(q)
            
        # 🔥 UPDATED: CHAT LOGIC (Step 4)
        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                reply = smart_ai_response(
                    user_msg=q,
                    risk=st.session_state.risk,
                    location=loc,
                    gemini_model=gemini
                )
                st.markdown(reply)
                st.session_state.chat_messages.append({"role":"assistant","content":reply})

with tab5:
    st.markdown("### 🌊 About FloodGuard AI")
    st.write("InnovateX Hackathon 2025 Project.")
    
