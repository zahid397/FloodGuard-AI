import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import joblib
import os
from utils.weather_api import get_weather_data
from utils.alert_system import send_sms_alert, send_telegram_alert
from utils.lang import get_text
import folium  # Bonus map
from streamlit_folium import folium_static

# Page config
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# Load model
@st.cache_resource
def load_model():
    return joblib.load('model/flood_model.pkl')

model = load_model()

# Language toggle
lang = st.sidebar.selectbox("Language / ভাষা", ["English", "বাংলা"])

# Header
st.title(get_text('title', lang))
st.markdown("**AI-Powered Flood Prediction & Community Alert System** | Powered by BUBT IT Club Hackathon 2025")

# Sidebar
st.sidebar.header("⚙️ Settings")
openweather_key = st.sidebar.text_input("OpenWeather API Key", type="password")
twilio_sid = st.sidebar.text_input("Twilio SID", type="password")
twilio_token = st.sidebar.text_input("Twilio Token", type="password")
telegram_bot = st.sidebar.text_input("Telegram Bot Token (Optional)", type="password")
telegram_chat = st.sidebar.text_input("Telegram Chat ID (Optional)", type="password")
phone_number = st.sidebar.text_input("Phone for SMS", value="+8801xxxxxxxxx")
city = st.sidebar.text_input("City", value="Dhaka")

# Predict function
def predict_flood(features):
    df = pd.DataFrame([features], columns=['rainfall', 'humidity', 'temperature', 'river_level', 'pressure'])
    prediction = model.predict(df)[0]
    probability = model.predict_proba(df)[0][1] * 100
    return "High Risk 🌊" if prediction == 1 else "Low Risk ✅", probability

# Main columns
col1, col2 = st.columns(2)

with col1:
    st.header("📊 Real-Time Data")
    if openweather_key:
        weather = get_weather_data(city, openweather_key)
        if weather:
            st.json(weather)
            risk_level, prob = predict_flood(list(weather.values()))
            st.metric(get_text('risk_level', lang), risk_level)
            st.progress(prob / 100)
            st.write(f"{get_text('prediction', lang)}: {prob:.1f}%")
        else:
            st.error("Invalid API Key!")
    else:
        st.info("Enter API Key for live data.")

with col2:
    st.header(get_text('alert', lang))
    if st.button(get_text('test_sms', lang)):
        if twilio_sid and twilio_token and phone_number:
            message = f"🚨 FloodGuard Alert: {risk_level} in {city}! Risk: {prob:.1f}%"
            if send_sms_alert(message, phone_number, "+15017122661", twilio_sid, twilio_token):
                st.success("SMS Sent! 📱")
            # Bonus Telegram
            if telegram_bot and telegram_chat:
                send_telegram_alert(message, telegram_bot, telegram_chat)
                st.success("Telegram Alert Sent! 🤖")
        else:
            st.warning("Enter credentials.")

# Visualization
st.header("📈 Flood Risk Visualization")
historical_data = pd.DataFrame({
    'Date': pd.date_range(start='2023-01-01', periods=30),
    'Rainfall': np.random.uniform(5, 35, 30),
    'Flood Risk %': np.random.uniform(0, 100, 30)
})
fig = px.line(historical_data, x='Date', y='Flood Risk %', title="Historical Flood Risk Trend")
fig.add_scatter(x=historical_data['Date'], y=historical_data['Rainfall'], mode='lines', name='Rainfall (mm)')
st.plotly_chart(fig, use_container_width=True)

# Bonus Map (Dhaka flood-prone areas)
if st.checkbox("Show Flood Map 🌍"):
    m = folium.Map(location=[23.8103, 90.4125], zoom_start=10)
    folium.Marker([23.8103, 90.4125], popup="Dhaka - High Risk Area").add_to(m)
    folium_static(m)

# Bilingual footer
if lang == "বাংলা":
    st.markdown("**বন্যা ঝুঁকি প্রেডিকশন:** AI মডেল ডেটা থেকে হিসাব করেছে।")
else:
    st.markdown("**Flood Risk Prediction:** AI model calculated from data.")

# Export
if st.button("📄 Export Report"):
    st.download_button("Download CSV", historical_data.to_csv(), "flood_report.csv")
    # PDF: Use reportlab for full, but simple here

# Footer
st.markdown("---")
st.markdown("*Built for InnovateX Hackathon 2025 | SDG 13 (Climate Action) & SDG 17 (Partnerships)*")
