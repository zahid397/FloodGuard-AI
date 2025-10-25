# 🌊 FloodGuard AI | Fixed 2025 Version
# Developed by Zahid Hasan 💻 | AI + Real Data + Bengali Voice

import streamlit as st
import pandas as pd
import pickle
import requests
import os
import folium
from streamlit_folium import st_folium
import plotly.express as px
from gtts import gTTS
from io import BytesIO
import base64
import google.generativeai as genai

# ================== Page Setup ==================
st.set_page_config(page_title="FloodGuard AI", page_icon="🌧️", layout="wide")
st.title("🌊 FloodGuard AI - Fixed 2025 Edition")
st.caption("💻 Developed by Zahid Hasan | Gemini 2.5 + Real Data + Bengali Voice")

# ================== Gemini Setup ==================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-2.0-flash")
except Exception as e:
    gemini_model = None
    st.warning(f"⚠️ Gemini not configured: {e}")

# ================== Model Load ==================
MODEL_PATH = "model/flood_model.pkl"
model = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
else:
    st.warning("⚠️ Flood model not found. Please train and add flood_model.pkl")

# ================== Sidebar Inputs ==================
st.sidebar.header("📥 Input Parameters")
rain = st.sidebar.number_input("Rainfall (mm)", 0.0, 500.0, 45.0)
temp = st.sidebar.number_input("Temperature (°C)", -10.0, 60.0, 27.0)
hum = st.sidebar.number_input("Humidity (%)", 0.0, 100.0, 82.0)
water = st.sidebar.number_input("River Level (m)", 0.0, 25.0, 5.0)
city = st.sidebar.text_input("🌍 City Name", "Dhaka")

# ================== OpenWeather API ==================
def get_weather(city):
    api_key = st.secrets.get("OPENWEATHER_API", "YOUR_API_KEY")
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url)
        data = r.json()

        if "name" not in data or "main" not in data:
            return {"error": data.get("message", "Invalid API response")}

        return {
            "City": data["name"],
            "Temperature": f"{data['main']['temp']} °C",
            "Humidity": f"{data['main']['humidity']}%",
            "Description": data["weather"][0]["description"].capitalize(),
        }
    except Exception as e:
        return {"error": str(e)}

# ================== BWDB Demo Data ==================
def get_bwdb_river_data():
    return {
        "Padma": {"level_m": 5.6, "status": "Rising"},
        "Jamuna": {"level_m": 6.2, "status": "Stable"},
        "Meghna": {"level_m": 4.1, "status": "Falling"},
    }

# ================== Flood Prediction ==================
if st.button("🔮 Predict Flood Risk"):
    if model:
        df = pd.DataFrame([[rain, temp, hum, water]],
                          columns=["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"])
        try:
            pred = model.predict(df)[0]
            risk = {0: "Low", 1: "Medium", 2: "High"}.get(int(pred), "Unknown")
            color = {"Low": "green", "Medium": "orange", "High": "red"}[risk]
            st.markdown(f"### 🧠 Predicted Flood Risk: <span style='color:{color}'>{risk}</span>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Prediction failed: {e}")
    else:
        st.warning("⚠️ Model not loaded.")

# ================== Live Weather & River Data ==================
st.divider()
st.subheader("📡 Live Weather & River Data")
st.json(get_weather(city))
st.json(get_bwdb_river_data())

# ================== Flood Map ==================
st.divider()
st.subheader("🗺️ Flood Map Visualization")
m = folium.Map(location=[23.685, 90.3563], zoom_start=7)
for river, loc in {"Padma": [23.7, 89.7], "Jamuna": [24.45, 89.7], "Meghna": [23.2, 90.6]}.items():
    folium.Marker(loc, tooltip=river).add_to(m)
st_folium(m, width=700, height=400)

# ================== Plotly Dashboard ==================
st.divider()
st.subheader("📊 Flood Risk Trend Dashboard")
data = {
    "Date": pd.date_range("2025-10-01", periods=10),
    "Risk_Level": [0, 1, 0, 2, 2, 1, 0, 1, 2, 1]
}
df_dash = pd.DataFrame(data)
fig = px.line(df_dash, x="Date", y="Risk_Level",
              title="Flood Risk Trends (Simulated)",
              markers=True)
st.plotly_chart(fig, use_container_width=True)

# ================== City Forecast Cards ==================
st.divider()
st.subheader("🧠 City-Sector Flood Forecast")
cols = st.columns(3)
for i, c in enumerate(["Dhaka", "Rajshahi", "Chittagong"]):
    with cols[i]:
        st.metric(label=c, value="Moderate Risk", delta="7-Day Forecast")

# ================== Gemini Chat + Memory ==================
st.divider()
st.subheader("💬 FloodGuard AI (Gemini 2.5 Chat)")
if "memory" not in st.session_state:
    st.session_state.memory = []

query = st.text_input("তোমার প্রশ্ন লিখো:")
if query:
    st.session_state.memory.append({"user": query})
    if gemini_model:
        with st.spinner("🤖 FloodGuard AI ভাবছে..."):
            # Safely build context
            context = " ".join([m.get("user", "") for m in st.session_state.memory[-3:]])
            response = gemini_model.generate_content(f"Context: {context}\nবাংলায় উত্তর দাও: {query}")
            ans = response.text
            st.markdown(f"**FloodGuard AI:** {ans}")
            st.session_state.memory.append({"ai": ans})
            # ===== Voice (gTTS) =====
            try:
                tts = gTTS(ans, lang="bn")
                audio = BytesIO()
                tts.write_to_fp(audio)
                audio.seek(0)
                b64 = base64.b64encode(audio.read()).decode()
                st.markdown(
                    f'<audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
                    unsafe_allow_html=True)
            except:
                st.warning("🎤 Voice playback unavailable.")
    else:
        st.error("⚠️ Gemini API unavailable.")

# ================== Footer ==================
st.divider()
st.caption("🌊 FloodGuard AI 2025 | Powered by Google Gemini + OpenWeather + BWDB + Bengali Voice 🎤")
