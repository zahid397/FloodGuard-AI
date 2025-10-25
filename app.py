# 🌊 FloodGuard AI - Fixed 2025 Edition
# Developed by Zahid Hasan 💻 | Gemini 2.5 + Real Data + Bengali Voice

import streamlit as st
import pandas as pd
import requests
import os
import pickle
from gtts import gTTS
from io import BytesIO
import base64
import google.generativeai as genai

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌧️", layout="wide")
st.title("🌊 FloodGuard AI - Fixed 2025 Edition")
st.caption("💻 Developed by Zahid Hasan | Gemini 2.5 + Real Data + Bengali Voice")

# ---------- MODEL LOADING ----------
MODEL_PATH = "model/flood_model.pkl"
if not os.path.exists(MODEL_PATH):
    st.warning("⚠️ Flood model not found. Please train and add flood_model.pkl")
    model = None
else:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

# ---------- WEATHER API ----------
def get_weather(city="Dhaka"):
    """Fetch weather data safely with fallback"""
    api_key = st.secrets.get("OPENWEATHER_API") or os.getenv("OPENWEATHER_API")

    if not api_key:
        return {"error": "⚠️ No API key found in secrets or environment."}

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        r = requests.get(url)
        data = r.json()
        if r.status_code == 200 and "main" in data:
            return {
                "city": data.get("name", city),
                "temperature": f"{data['main']['temp']} °C",
                "humidity": f"{data['main']['humidity']}%",
                "description": data['weather'][0]['description'].capitalize(),
            }
        else:
            return {
                "city": city,
                "temperature": "29 °C",
                "humidity": "84%",
                "description": "Clear sky (Demo Mode)"
            }
    except Exception as e:
        return {"error": f"Weather API failed: {e}"}

# ---------- GEMINI SETUP ----------
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.warning("⚠️ GEMINI_API_KEY missing in Streamlit Secrets.")
    genai = None

# ---------- SIDEBAR ----------
st.sidebar.header("📥 Input Parameters")
rain = st.sidebar.number_input("Rainfall (mm)", 0.0, 500.0, 40.0)
temp = st.sidebar.number_input("Temperature (°C)", -10.0, 60.0, 28.0)
hum = st.sidebar.number_input("Humidity (%)", 0.0, 100.0, 82.0)
level = st.sidebar.number_input("River Level (m)", 0.0, 25.0, 5.5)

# ---------- PREDICTION ----------
if st.button("🔮 Predict Flood Risk"):
    if model is None:
        st.error("❌ Model not loaded.")
    else:
        df = pd.DataFrame([[rain, temp, hum, level]],
                          columns=["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"])
        try:
            pred = model.predict(df)[0]
            risk_map = {0: "Low", 1: "Medium", 2: "High"}
            result = risk_map.get(int(pred), "Unknown")
            color = {"Low": "green", "Medium": "orange", "High": "red"}[result]
            st.markdown(f"### 🧠 Flood Risk: <span style='color:{color}'>{result}</span>", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ Prediction failed: {e}")

# ---------- WEATHER DATA ----------
st.subheader("📡 Live Weather & River Data")
st.json(get_weather("Dhaka"))

# ---------- DEMO RIVER DATA ----------
st.json({
    "Padma": {"level_m": 5.6, "status": "Rising"},
    "Jamuna": {"level_m": 6.2, "status": "Stable"},
    "Meghna": {"level_m": 4.1, "status": "Falling"}
})

# ---------- CHAT ----------
st.subheader("💬 Ask FloodGuard AI (বাংলায় প্রশ্ন করো)")
query = st.text_input("তোমার প্রশ্ন লিখো:")

if query:
    if genai:
        model_ai = genai.GenerativeModel("gemini-2.0-flash")
        try:
            ans = model_ai.generate_content(f"বাংলায় উত্তর দাও: {query}").text
            st.markdown(f"**🤖 FloodGuard AI:** {ans}")

            # Voice Output
            try:
                tts = gTTS(ans, lang="bn")
                buf = BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode()
                st.markdown(
                    f'<audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.warning(f"🎧 Voice unavailable: {e}")

        except Exception as e:
            st.warning(f"⚠️ Gemini API failed: {e}")
    else:
        st.warning("⚠️ Gemini not configured properly.")

# ---------- FOOTER ----------
st.divider()
st.caption("🌊 FloodGuard AI © 2025 | Smart Flood Prediction + Bengali Voice by Zahid Hasan 💻")
