# FloodGuard AI 🌊 | Full Streamlit App
# Developed by Zahid Hasan

import streamlit as st
import pandas as pd
import pickle
import os
import sys
import datetime
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import st_folium
import folium

# ===== 🌊 Page Config =====
st.set_page_config(page_title="FloodGuard AI", page_icon="🌧️", layout="wide")

# ===== 🔁 Auto Refresh =====
st_autorefresh(interval=30000, key="data_refresh")  # Refresh every 30 seconds

# ===== ✅ Import Path Fix =====
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

# ===== 🧩 Try Importing Helper Modules =====
try:
    from utils.weather_api import get_weather_data
except Exception:
    get_weather_data = None

try:
    from utils.river_api import get_river_data
except Exception:
    get_river_data = None

try:
    from model.train_model import train_model
except Exception:
    train_model = None

# ===== ⚙️ Model Load =====
MODEL_PATH = "model/flood_model.pkl"
model = None

if not os.path.exists(MODEL_PATH):
    st.warning("⚠️ Model not found! Training a new one...")
    if train_model:
        try:
            train_model()
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            st.success("✅ Model trained successfully!")
        except Exception as e:
            st.error(f"❌ Model training failed: {e}")
    else:
        st.error("❌ train_model() not found. Please check 'model/train_model.py'.")
else:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

# ===== 🌆 Sidebar =====
st.sidebar.header("📍 Input Parameters")

city = st.sidebar.selectbox(
    "Select City",
    ["Dhaka", "Rajshahi", "Sylhet", "Khulna", "Chattogram", "Barishal", "Rangpur"]
)

rainfall = st.sidebar.number_input("Rainfall (mm)", min_value=0.0, max_value=500.0, step=1.0)
temperature = st.sidebar.number_input("Temperature (°C)", min_value=-10.0, max_value=60.0, step=0.5)
humidity = st.sidebar.number_input("Humidity (%)", min_value=0.0, max_value=100.0, step=1.0)
river_level = st.sidebar.number_input("River Level (m)", min_value=0.0, max_value=25.0, step=0.1)

# ===== 🌊 App Title =====
st.title("🌊 FloodGuard AI - Smart Flood Prediction System")
st.write("এই অ্যাপটি রিয়েল-টাইম আবহাওয়া ও নদীর তথ্য বিশ্লেষণ করে বন্যার ঝুঁকি অনুমান করে।")

# ===== 🔮 Flood Prediction =====
if st.button("🔮 Predict Flood Risk"):
    if model is None:
        st.error("❌ Model not loaded. Please ensure 'flood_model.pkl' exists.")
    else:
        input_data = pd.DataFrame(
            [[rainfall, temperature, humidity, river_level]],
            columns=["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"]
        )
        try:
            pred = model.predict(input_data)[0]
            if pred == 2:
                st.error("🚨 HIGH RISK: Flood likely to occur! Stay alert.")
                st.toast("🚨 Flood Alert! Evacuate low-lying areas.")
            elif pred == 1:
                st.warning("⚠️ MEDIUM RISK: Monitor water levels closely.")
            else:
                st.success("✅ LOW RISK: No flood expected.")
        except Exception as e:
            st.warning(f"⚠️ Prediction failed: {e}")

# ===== 🧠 Flood Risk History =====
if os.path.exists("data/flood_history.csv"):
    st.subheader("📜 Flood Risk History")
    hist = pd.read_csv("data/flood_history.csv")
    st.dataframe(hist.tail(10), use_container_width=True)
else:
    st.info("ℹ️ No flood history data available yet.")

# ===== 🌦️ Live Weather Data =====
if st.checkbox("📡 Show Live Weather & River Data"):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌦 Weather Data")
        if get_weather_data:
            weather = get_weather_data(city)
            if "error" not in weather:
                st.metric("🌡️ Temperature (°C)", weather["temperature"])
                st.metric("💧 Humidity (%)", weather["humidity"])
                st.metric("🌧️ Rainfall (mm)", weather["rain"])
                st.metric("🌤️ Condition", weather["description"])
            else:
                st.warning(weather["error"])
        else:
            st.info("Weather API not integrated yet.")

    with col2:
        st.subheader("🌊 River Data")
        if get_river_data:
            river = get_river_data(city)
            if "error" not in river:
                st.json(river)
            else:
                st.warning(river["error"])
        else:
            st.info("River API not integrated yet.")

# ===== 🗺️ Flood Map Visualization =====
st.subheader("🗺️ Flood Map Visualization")
m = folium.Map(location=[23.685, 90.3563], zoom_start=6)

# Padma, Meghna, Jamuna marker
rivers = {
    "Padma": [23.5, 89.8],
    "Meghna": [23.3, 90.7],
    "Jamuna": [24.5, 89.6]
}
for name, coord in rivers.items():
    folium.Marker(location=coord, popup=f"{name} River").add_to(m)

st_folium(m, width=700, height=450)

# ===== 💬 Chat Section =====
st.subheader("💬 Ask FloodGuard AI")
user_msg = st.text_input("Type your question:")
if user_msg:
    st.write(f"🤖 FloodGuard AI: Data-based insight not ready yet, but '{user_msg}' logged for training!")

# ===== 📘 About Section =====
with st.expander("📘 About FloodGuard AI"):
    st.markdown("""
    **FloodGuard AI** একটি AI-চালিত বন্যা পূর্বাভাস এবং সতর্কতা সিস্টেম।
    এটি আবহাওয়া তথ্য, নদীর স্তর, এবং স্থানীয় ডেটা ব্যবহার করে
    বন্যার সম্ভাবনা নির্ধারণ করে। 🇧🇩  

    🔹 **Features:**  
    - Real-time Weather & River Data  
    - Flood Prediction (Low/Medium/High)  
    - Live Map of Major Rivers  
    - Auto Alerts & Notifications  
    - Chat Interface  
    - Flood History Tracking  

    🔹 **Developed by:** Zahid Hasan  
    🔹 **Powered by:** Streamlit + Python + AI
    """)

# ===== 🕒 Footer =====
st.caption(f"⏱️ Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💻 Developed by Zahid Hasan | 🌊 FloodGuard AI © 2025")
