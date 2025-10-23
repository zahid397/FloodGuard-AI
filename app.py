import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import requests
from dotenv import load_dotenv
from twilio.rest import Client
import folium
from streamlit_folium import st_folium

# ===============================
# 🌍 CONFIG LOAD
# ===============================
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
ALERT_PHONE = os.getenv("ALERT_PHONE")
RIVER_API_URL = os.getenv("RIVER_API_URL", "http://127.0.0.1:5000/rivers")

# ===============================
# 🌊 APP TITLE
# ===============================
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="centered")
st.title("🌊 FloodGuard AI – Bangladesh Flood Risk Predictor")

# ===============================
# 📦 LOAD MODEL
# ===============================
model_path = "model/flood_model.pkl"
if not os.path.exists(model_path):
    st.error("⚠️ Model not found! Please run train_model.py first.")
    st.stop()
model = joblib.load(model_path)

# ===============================
# 🌦 WEATHER API FUNCTION
# ===============================
def get_weather(lat, lon):
    if not OPENWEATHER_API_KEY:
        st.warning("❌ No OpenWeather API key found.")
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        data = requests.get(url).json()
        return {
            "rainfall": data.get("rain", {}).get("1h", 0),
            "humidity": data["main"]["humidity"],
            "temperature": data["main"]["temp"],
            "pressure": data["main"]["pressure"]
        }
    except Exception as e:
        st.error(f"Weather API Error: {e}")
        return None

# ===============================
# 🌊 RIVER API FUNCTION
# ===============================
def get_river_data(river_name):
    try:
        res = requests.get(RIVER_API_URL)
        df = pd.DataFrame(res.json())
        river = df[df["River Name"].str.lower() == river_name.lower()]
        if river.empty:
            st.warning("❌ River not found in database.")
            return None
        return river.iloc[0].to_dict()
    except Exception as e:
        st.error(f"River API Error: {e}")
        return None

# ===============================
# 📲 TWILIO ALERT SYSTEM
# ===============================
def send_flood_alert(message):
    if not (TWILIO_SID and TWILIO_AUTH):
        st.warning("⚠️ Twilio credentials missing.")
        return
    try:
        client = Client(TWILIO_SID, TWILIO_AUTH)
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=ALERT_PHONE
        )
        st.success("📩 Alert SMS sent successfully!")
    except Exception as e:
        st.error(f"Twilio Error: {e}")

# ===============================
# 🧭 MAP FUNCTION
# ===============================
def show_flood_map(lat, lon, flood_risk):
    m = folium.Map(location=[lat, lon], zoom_start=7)
    color = "red" if flood_risk else "green"
    folium.Marker(
        [lat, lon],
        popup=f"Flood Risk: {'High' if flood_risk else 'Low'}",
        icon=folium.Icon(color=color)
    ).add_to(m)
    st_folium(m, width=700, height=450)

# ===============================
# 🧮 INPUT SECTION
# ===============================
st.subheader("📥 Input Environmental Data")

col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("Latitude", value=23.685, format="%.4f")
    rainfall = st.number_input("Rainfall (mm)", min_value=0.0, max_value=1000.0, value=200.0)
    river_name = st.text_input("River Name (optional)", placeholder="e.g. Jamuna")
with col2:
    lon = st.number_input("Longitude", value=90.3563, format="%.4f")
    humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=80.0)
    temperature = st.number_input("Temperature (°C)", min_value=0.0, max_value=50.0, value=30.0)

river_level = st.number_input("River Level (m)", min_value=0.0, max_value=20.0, value=5.0)
pressure = st.number_input("Atmospheric Pressure (hPa)", min_value=900.0, max_value=1100.0, value=1010.0)

# ===============================
# 🔍 AUTO FETCH WEATHER
# ===============================
if st.button("🌦 Auto-Fetch from OpenWeather"):
    weather = get_weather(lat, lon)
    if weather:
        st.write(weather)
        rainfall = weather["rainfall"]
        humidity = weather["humidity"]
        temperature = weather["temperature"]
        pressure = weather["pressure"]

# ===============================
# 🚀 PREDICT BUTTON
# ===============================
if st.button("🔍 Predict Flood Risk"):
    data = np.array([[rainfall, humidity, temperature, river_level, pressure]])
    prediction = model.predict(data)[0]
    flood_risk = prediction >= 0.5

    if flood_risk:
        st.error("🚨 High Flood Risk Detected!")
        send_flood_alert("🚨 FloodGuard Alert: High flood risk detected! Stay safe.")
    else:
        st.success("✅ Low Flood Risk (Safe Zone)")

    if river_name:
        river_data = get_river_data(river_name)
        if river_data:
            st.info(f"🌊 River Info: {river_data['River Name']} • Zone: {river_data['BWDB Zone']} • Type: {river_data['Flow Type']}")

    show_flood_map(lat, lon, flood_risk)

st.markdown("---")
st.caption("Developed by Zahid Hasan • Powered by AI 🌎")
