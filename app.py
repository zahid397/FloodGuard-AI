import streamlit as st
import pandas as pd
import pickle
import os
import sys

# ===== ✅ Fix Import Path (for Streamlit Cloud & Local both) =====
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

# ===== 🧩 Try Importing from utils =====
try:
    from utils.weather_api import get_weather_data
except ModuleNotFoundError:
    get_weather_data = None

try:
    from utils.river_api import get_river_data
except ModuleNotFoundError:
    get_river_data = None

try:
    from model.train_model import train_model
except ModuleNotFoundError:
    train_model = None

# ===== ⚙️ Model Path =====
MODEL_PATH = "model/flood_model.pkl"

# ===== 🧠 Load or Train Model =====
if not os.path.exists(MODEL_PATH):
    st.warning("⚠️ Model not found! Training a new one...")
    if train_model:
        train_model()
    else:
        st.error("❌ train_model function not found. Please check model/train_model.py.")
else:
    with open(MODEL_PATH, "rb") as file:
        model = pickle.load(file)

# ===== 🌊 Streamlit UI =====
st.set_page_config(page_title="FloodGuard AI", page_icon="🌧️", layout="centered")

st.title("🌊 FloodGuard AI - Smart Flood Prediction System")
st.write("এই অ্যাপটি রিয়েল-টাইম আবহাওয়া ও নদীর তথ্য বিশ্লেষণ করে বন্যার ঝুঁকি অনুমান করে।")

# ===== 🧾 Sidebar Input =====
st.sidebar.header("📥 Input Parameters")

rainfall = st.sidebar.number_input("Rainfall (mm)", min_value=0.0, max_value=500.0, step=1.0)
temperature = st.sidebar.number_input("Temperature (°C)", min_value=0.0, max_value=50.0, step=0.5)
humidity = st.sidebar.number_input("Humidity (%)", min_value=0.0, max_value=100.0, step=1.0)
river_level = st.sidebar.number_input("River Level (m)", min_value=0.0, max_value=20.0, step=0.1)

# ===== 🔮 Prediction Button =====
if st.button("🔮 Predict Flood Risk"):
    if 'model' not in locals():
        st.error("❌ Model not loaded. Please check if 'flood_model.pkl' exists.")
    else:
        input_data = pd.DataFrame([[rainfall, temperature, humidity, river_level]],
                                  columns=["rainfall", "temperature", "humidity", "river_level"])
        prediction = model.predict(input_data)[0]

        if prediction == 1:
            st.error("🚨 High Risk: Flood likely to occur!")
        else:
            st.success("✅ Low Risk: No flood expected.")

# ===== 🌦️ Optional: Live Data =====
if st.checkbox("Show Live Weather & River Data"):
    st.subheader("🌦 Current Weather Data")
    if get_weather_data:
        try:
            weather = get_weather_data()
            st.json(weather)
        except Exception as e:
            st.warning(f"Weather API not available: {e}")
    else:
        st.info("Weather API not integrated yet.")

    st.subheader("🌊 River Data")
    if get_river_data:
        try:
            river = get_river_data()
            st.json(river)
        except Exception as e:
            st.warning(f"River API not available: {e}")
    else:
        st.info("River API not integrated yet.")

# ===== 👇 Footer =====
st.caption("Developed by Zahid Hasan 💻 | Powered by Streamlit 🌊")
