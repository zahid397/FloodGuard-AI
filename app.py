# FloodGuard AI 🌊 | Streamlit Frontend
# Developed by Zahid Hasan

import streamlit as st
import pandas as pd
import pickle
import os
import sys
from streamlit_autorefresh import st_autorefresh

# ===== 🌊 Streamlit Page Config (must be first) =====
st.set_page_config(
    page_title="FloodGuard AI",
    page_icon="🌧️",
    layout="centered"
)

# ===== 🔁 Auto Refresh Every 30 Seconds =====
st_autorefresh(interval=30000, key="data_refresh")  # Refresh every 30 sec

# ===== ✅ Fix Import Path =====
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

# ===== ⚙️ Model Path =====
MODEL_PATH = "model/flood_model.pkl"

# ===== 🧠 Load or Train Model =====
model = None
if not os.path.exists(MODEL_PATH):
    st.warning("⚠️ Model not found! Training a new one...")
    if train_model:
        try:
            train_model()
            with open(MODEL_PATH, "rb") as file:
                model = pickle.load(file)
            st.success("✅ Model trained successfully!")
        except Exception as e:
            st.error(f"❌ Model training failed: {e}")
    else:
        st.error("❌ train_model() not found. Please check 'model/train_model.py'.")
else:
    try:
        with open(MODEL_PATH, "rb") as file:
            model = pickle.load(file)
    except Exception as e:
        st.error(f"❌ Failed to load model: {e}")

# ===== 🌊 App Title & Description =====
st.title("🌊 FloodGuard AI - Smart Flood Prediction System")
st.write("এই অ্যাপটি রিয়েল-টাইম আবহাওয়া ও নদীর তথ্য বিশ্লেষণ করে বন্যার ঝুঁকি অনুমান করে।")

# ===== 🧾 Sidebar Inputs =====
st.sidebar.header("📥 Input Parameters")

rainfall = st.sidebar.number_input("Rainfall (mm)", min_value=0.0, max_value=500.0, step=1.0)
temperature = st.sidebar.number_input("Temperature (°C)", min_value=-10.0, max_value=60.0, step=0.5)
humidity = st.sidebar.number_input("Humidity (%)", min_value=0.0, max_value=100.0, step=1.0)
river_level = st.sidebar.number_input("River Level (m)", min_value=0.0, max_value=25.0, step=0.1)

# ===== 🔮 Prediction Section =====
if st.button("🔮 Predict Flood Risk"):
    if model is None:
        st.error("❌ Model not loaded. Please ensure 'flood_model.pkl' exists.")
    else:
        # ✅ Correct column names (match training data)
        input_data = pd.DataFrame(
            [[rainfall, temperature, humidity, river_level]],
            columns=["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"]
        )

        try:
            prediction = model.predict(input_data)[0]
            if prediction == 2:
                st.error("🚨 HIGH RISK: Flood likely to occur! Stay alert.")
            elif prediction == 1:
                st.warning("⚠️ MEDIUM RISK: Monitor water levels closely.")
            else:
                st.success("✅ LOW RISK: No flood expected.")
        except Exception as e:
            st.warning(f"⚠️ Prediction failed: {e}")

# ===== 🌦️ Optional: Live Data Section =====
if st.checkbox("📡 Show Live Weather & River Data"):
    st.subheader("🌦 Current Weather Data")
    if get_weather_data:
        try:
            weather = get_weather_data("Dhaka")
            if "error" in weather:
                st.warning(weather["error"])
            else:
                st.json(weather)
        except Exception as e:
            st.warning(f"Weather API not available: {e}")
    else:
        st.info("ℹ️ Weather API not integrated yet.")

    st.subheader("🌊 River Data")
    if get_river_data:
        try:
            river = get_river_data("Bangladesh")
            if "error" in river:
                st.warning(river["error"])
            else:
                st.json(river)
        except Exception as e:
            st.warning(f"River API not available: {e}")
    else:
        st.info("ℹ️ River API not integrated yet.")

# ===== ⏱️ Last Updated Info =====
import datetime
st.caption(f"⏱️ Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Auto-refresh every 30s)")

# ===== 👇 Footer =====
st.caption("Developed by Zahid Hasan 💻 | Powered by Streamlit 🌊")
