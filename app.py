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
import joblib  # Using joblib as in your original
import requests
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- THEME (Your theme is great) ----------
st.markdown("""
<style>
.stApp {background-color:#ffffff!important;color:#0a192f!important;font-family:"Segoe UI",sans-serif!important;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#0078d7,#0099ff)!important;border-right:3px solid #005a9e!important;}
[data-testid="stSidebar"] * {color:#ffffff!important;font-weight:600!important;}
div[data-baseweb="select"], div[data-baseweb="select"]>div {background:#ffffff!important;color:#0a192f!important;border:2px solid #005a9e!important;border-radius:8px!important;font-weight:600!important;}
.stButton>button {background:#0078d7!important;color:white!important;border-radius:6px!important;font-weight:600!important;border:none!important;}
.stButton>button:hover {background:#005a9e!important;transform:scale(1.03);}
.weather-box {background:#f8fbff!important;border:2px solid #0078d7!important;border-radius:8px!important;padding:10px!important;font-weight:600!important;}
[data-testid="stChatInput"] textarea {background:#ffffff!important;border:2px solid #0078d7!important;border-radius:8px!important;color:#1a1a1a!important;}
[data-testid="stChatMessage"] {background:#f4faff!important;border-radius:10px!important;padding:10px!important;margin-bottom:5px!important;}
.leaflet-container {height:520px!important;border-radius:10px!important;box-shadow:0 4px 8px rgba(0,0,0,0.15)!important;}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<h1 style='text-align:center;'>🌊 FloodGuard AI – InnovateX Hackathon 2025</h1>", unsafe_allow_html=True)
st.caption("💻 Team Project | XGBoost ML | Gemini 2.5 Flash | Voice Chatbot | SDG 13 & 17")

# ---------- SESSION STATE (Robust) ----------
if 'risk' not in st.session_state:
    st.session_state.risk = "N/A"
if 'ai_summary' not in st.session_state:
    st.session_state.ai_summary = None
if 'audio' not in st.session_state:
    st.session_state.audio = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'weather_data' not in st.session_state:
    # This state holds weather data to avoid multiple API calls
    st.session_state.weather_data = {"temp": 25.9, "hum": 83, "rain": 0}
if 'prediction_inputs' not in st.session_state:
    st.session_state.prediction_inputs = None

# ---------- LOAD MODEL ----------
@st.cache_resource
def load_model():
    try:
        model = joblib.load("model/flood_model.pkl")
        st.success("✅ ML Model Loaded (XGBoost)")
        return model
    except Exception:
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
            try:
                # Try to get the latest model
                gmodel = genai.GenerativeModel("gemini-1.5-flash") # Using 1.5-flash for stability
            except Exception:
                gmodel = genai.GenerativeModel("gemini-pro") # Fallback
            st.success("✅ Gemini Connected Successfully")
            return gmodel
    except Exception as e:
        st.warning(f"Gemini setup failed: {e}")
    return None
gemini = init_gemini()

# ---------- WEATHER API ----------
def get_weather(city, api_key, slider_fallbacks):
    """Fetches weather or uses slider data as fallback."""
    if not api_key:
        return slider_fallbacks["temp"], slider_fallbacks["hum"], slider_fallbacks["rain"]
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=5).json()
        if r.get("cod") == 200:
            temp = r["main"]["temp"]
            hum = r["main"]["humidity"]
            rain = r.get("rain", {}).get("1h", 0) # 1-hour rainfall
            return temp, hum, rain
    except Exception:
        pass # Fallthrough to slider data
    return slider_fallbacks["temp"], slider_fallbacks["hum"], slider_fallbacks["rain"]

# ---------- FLOOD PREDICTION (Fixed Inputs) ----------
def predict_flood(features):
    """Predicts flood risk using ML model or fallback."""
    if model:
        try:
            # Ensure columns match your trained model
            df = pd.DataFrame([features], columns=["rainfall", "humidity", "temperature", "river_level", "pressure"])
            # Get probability of "Flood" (class 1)
            prob = model.predict_proba(df)[0][1] * 100
            risk = "High" if prob > 70 else "Medium" if prob > 30 else "Low"
            return f"{risk} ({prob:.1f}%)"
        except Exception as e:
            st.error(f"Model prediction error: {e}. Check model features.")
            # Fallback if model features mismatch
            
    # Fallback logic (uses first 4 features)
    s = (features[0]/100) + (features[3]/8) + (features[1]/100) - (features[2]/40)
    risk = "High" if s > 2 else "Medium" if s > 1 else "Low"
    return f"{risk} (Rule-Based)"

# ---------- PDF EXPORT (Robust) ----------
def create_pdf_report(risk, weather, summary, inputs):
    """Generates a PDF report from session state data."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, "FloodGuard AI Report")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 720, "Location:")
    c.setFont("Helvetica", 12)
    c.drawString(150, 720, inputs['loc'])
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 700, "Predicted Risk:")
    c.setFont("Helvetica", 12)
    c.drawString(150, 700, risk)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 670, "Weather & Input Data:")
    c.setFont("Helvetica", 12)
    c.drawString(60, 650, f"- Temperature: {weather['temp']:.1f}°C")
    c.drawString(60, 635, f"- Humidity: {weather['hum']:.0f}%")
    c.drawString(60, 620, f"- Rainfall (API/Input): {weather['rain']:.1f}mm")
    c.drawString(60, 605, f"- River Level (Input): {inputs['level']:.1f}m")
    c.drawString(60, 590, f"- Pressure (Input): {inputs['pressure']:.0f} hPa")

    if summary and summary != "LOADING":
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 560, "AI Safety Tips:")
        c.setFont("Helvetica", 10)
        text = summary[:500] # Limit length
        lines = [text[i:i+90] for i in range(0, len(text), 90)] # Wrap text
        y = 540
        for line in lines:
            c.drawString(60, y, line)
            y -= 15
            
    c.save()
    buf.seek(0)
    return buf

# ---------- SIDEBAR ----------
st.sidebar.header("📥 Flood Risk Inputs")
ow_key = st.sidebar.text_input("OpenWeather API Key (Optional)", type="password", help="For live weather data")
loc = st.sidebar.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])

st.sidebar.divider()
st.sidebar.markdown("#### Manual Data Overrides")
rain_slider = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50, help="Used if API key is missing")
temp_slider = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27, help="Used if API key is missing")
hum_slider = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85, help="Used if API key is missing")
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
# (FIX 3) Added Pressure slider to match your 5-feature model
pressure = st.sidebar.slider("💨 Pressure (hPa)", 950, 1050, 1013, help="Atmospheric pressure")

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    # Get live weather OR slider fallbacks
    slider_data = {"temp": temp_slider, "hum": hum_slider, "rain": rain_slider}
    temp_w, hum_w, rain_w = get_weather(loc, ow_key, slider_data)
    
    # Store weather and inputs in session state
    st.session_state.weather_data = {"temp": temp_w, "hum": hum_w, "rain": rain_w}
    st.session_state.prediction_inputs = {
        "rain": rain_w, "hum": hum_w, "temp": temp_w, "level": level, "pressure": pressure, "loc": loc
    }
    
    # Predict
    features = [rain_w, hum_w, temp_w, level, pressure]
    st.session_state.risk = predict_flood(features)
    
    # (FIX 1) Set AI to "LOADING" state. This makes the UI non-blocking.
    # The AI generation will happen in the main panel.
    st.session_state.ai_summary = "LOADING"
    st.session_state.audio = None
    st.rerun()

# ---------- MAIN CONTENT ----------

# --- 1. Prediction & AI Summary (Non-Blocking) ---
st.subheader("🔮 Flood Risk Analysis")
if st.session_state.risk != "N/A":
    risk_level = st.session_state.risk.split(" ")[0] # Get "High", "Medium", or "Low"
    color = {"Low":"#43a047", "Medium":"#fb8c00", "High":"#e53935"}.get(risk_level, "#0a192f")
    
    st.markdown(f"<h3>📍 {st.session_state.prediction_inputs['loc']} — Predicted Risk: <span style='color:{color};'>{st.session_state.risk}</span></h3>", unsafe_allow_html=True)

    # (FIX 1 Continued) AI Generation happens here, inside a spinner
    if st.session_state.ai_summary == "LOADING":
        with st.spinner("🤖 Gemini is analyzing the risk and generating advice..."):
            if gemini:
                try:
                    p = st.session_state.prediction_inputs
                    # (FIX 4) Specific prompt for reliable audio
                    prompt = f"Flood risk is {st.session_state.risk} for {p['loc']} (Rain: {p['rain']}mm, Level: {p['level']}m). Provide 2 short, vital safety tips. IMPORTANT: Start your ENTIRE reply *immediately* with the Bengali tips, followed by English. Example: '১. [Bengali Tip 1]\n২. [Bengali Tip 2]\n\n1. [English Tip 1]\n2. [English Tip 2]'"
                    
                    res = gemini.generate_content(prompt)
                    txt = res.text.strip()
                    st.session_state.ai_summary = txt
                    
                    # Generate audio from the first 2 lines (which *should* be Bengali now)
                    bangla_text = "\n".join(txt.split('\n')[:2])[:150] # Get first two lines
                    tts = gTTS(bangla_text, lang="bn", slow=False)
                    buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
                    st.session_state.audio = buf.getvalue()
                except Exception as e:
                    st.session_state.ai_summary = f"AI Error: {e}"
            else:
                st.session_state.ai_summary = "AI is not connected. Please check API key."

    # Display AI summary and audio
    if st.session_state.ai_summary and st.session_state.ai_summary != "LOADING":
        st.info(st.session_state.ai_summary)
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3")

else:
    st.info("⬅️ Please set your parameters in the sidebar and click 'Predict Flood Risk'")

# --- 2. Live Weather & River Status ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("☁️ Live Weather Report")
    w = st.session_state.weather_data
    st.markdown(f"<div class='weather-box'>📍 {st.session_state.prediction_inputs['loc'] if st.session_state.prediction_inputs else 'Dhaka'} | 🌡️ {w['temp']:.1f}°C | 💧 {w['hum']:.0f}% | 🌧️ {w['rain']:.1f}mm/h</div>", unsafe_allow_html=True)
    
with col2:
    st.subheader("📄 Download Report")
    if st.button("📄 Export Full Report as PDF"):
        if st.session_state.risk == "N/A":
            st.error("You must run a prediction first to generate a report.")
        else:
            pdf_buf = create_pdf_report(
                st.session_state.risk,
                st.session_state.weather_data,
                st.session_state.ai_summary,
                st.session_state.prediction_inputs
            )
            st.download_button("⬇️ Download PDF", pdf_buf, file_name="flood_report.pdf", mime="application/pdf")

st.divider()

# --- 3. River Status & Trend Chart ---
col3, col4 = st.columns([1, 2])
with col3:
    st.subheader("🌊 River Status")
    rivers = [
        {"River":"Padma","Station":"Goalundo","Level":round(8.7 + np.random.uniform(-0.2, 0.2),1),"Danger":10.5},
        {"River":"Jamuna","Station":"Sirajganj","Level":round(9.3 + np.random.uniform(-0.2, 0.2),1),"Danger":11.0},
        {"River":"Meghna","Station":"Ashugonj","Level":round(7.8 + np.random.uniform(-0.2, 0.2),1),"Danger":9.2},
    ]
    df_river = pd.DataFrame(rivers)
    df_river["Risk"] = np.where(df_river["Level"]>df_river["Danger"],"High",
                        np.where(df_river["Level"]>df_river["Danger"]*0.9,"Medium","Low"))
    st.dataframe(df_river, use_container_width=True, hide_index=True)
    
with col4:
    st.subheader("📊 30-Day Risk Trend")
    dates = pd.date_range(datetime.now()-timedelta(days=29), periods=30)
    rain_vals = np.clip(50+30*np.sin(np.linspace(0,3,30))+np.random.normal(0,10,30),0,200)
    risk_vals = ["Low" if rv<60 else "Medium" if rv<120 else "High" for rv in rain_vals]
    df_trend = pd.DataFrame({"Date":dates,"Rainfall (mm)":rain_vals,"Risk":risk_vals})
    fig = px.line(df_trend, x="Date", y="Rainfall (mm)", color="Risk",
                  color_discrete_map={"Low":"#43a047","Medium":"#fb8c00","High":"#e53935"},
                  title="Rainfall vs Flood Risk Trend (Simulation)")
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0)) # Compact
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 4. Map & Chatbot ---
col5, col6 = st.columns(2)
with col5:
    st.subheader("🗺️ Flood Risk Heatmap (Dhaka Focus)")
    m = folium.Map(location=[23.81, 90.41], zoom_start=10, tiles="CartoDB Positron")
    # More realistic heatmap points for Dhaka
    heat_points = [
        [23.723, 90.408, 0.8], [23.709, 90.415, 0.7], # Old Dhaka / Low-lying
        [23.810, 90.412, 0.5], [23.867, 90.384, 0.4], # Uttara / Mirpur
        [23.780, 90.420, 0.6], [23.75, 90.39, 0.5]  # Gulshan / Tejgaon
    ]
    HeatMap(heat_points, radius=20, blur=15, min_opacity=0.4).add_to(m)
    st_folium(m, width="100%", height=520) # Height fixed by CSS

with col6:
    st.subheader("💬 FloodGuard AI Chatbot (With Memory)")
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if q := st.chat_input("Ask a question / প্রশ্ন করুন..."):
        # User message
        st.session_state.messages.append({"role":"user", "content":q})
        with st.chat_message("user"):
            st.markdown(q)
        
        # Assistant message
        with st.chat_message("assistant"):
            if gemini:
                with st.spinner("AI is thinking..."):
                    try:
                        # (FIX 2) Provide chat history to Gemini
                        system_prompt = f"You are FloodGuard AI, a helpful expert on Bangladesh floods. The user's current predicted risk is '{st.session_state.risk}'. Use this context and the chat history to answer the user's *latest* question. Reply in both Bangla and English (shortly)."
                        
                        # Format history for Gemini
                        history_for_prompt = []
                        for m in st.session_state.messages:
                            history_for_prompt.append({"role": m["role"], "parts": [m["content"]]})
                        
                        # Start chat with history (all *except* the latest user query)
                        chat = gemini.start_chat(history=history_for_prompt[:-1])
                        
                        # Send the new query with the system prompt
                        reply_res = chat.send_message(f"{system_prompt}\n\nUSER'S LATEST QUESTION: {q}")
                        reply = reply_res.text
                    except Exception as e:
                        reply = f"AI Error: {e}"
            else:
                reply = f"Demo mode active — Risk: {st.session_state.risk}. Example: বন্যায় উঁচু জায়গায় থাকুন / Stay on high ground."
            
            st.markdown(reply)
            st.session_state.messages.append({"role":"assistant", "content":reply})
            
            # Voice for chat (best effort)
            try:
                # Try to find a Bengali line to read
                bangla_line = ""
                for line in reply.split('\n'):
                    if any('\u0980' <= char <= '\u09FF' for char in line):
                        bangla_line = line
                        break
                tts_text = bangla_line if bangla_line else reply.split('\n')[0]
                
                tts = gTTS(tts_text[:150], lang="bn", slow=False)
                buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
                st.audio(buf.getvalue(), format="audio/mp3")
            except Exception:
                pass # Non-critical if TTS fails

    if st.button("🗑️ Clear Chat History", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

# ---------- FOOTER ----------
st.divider()
st.markdown("<p style='text-align:center;font-weight:600;'>🌊 FloodGuard AI © 2025 | Gemini Flash | Team Project 💻</p>", unsafe_allow_html=True)
    
