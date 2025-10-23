import streamlit as st
import pandas as pd
import pickle
import os
from utils.weather_api import get_weather_data  # তোমার weather_api.py থেকে
from utils.river_api import get_river_data      # যদি থাকে
from model.train_model import train_model       # মডেল ট্রেন করার জন্য (ঐচ্ছিক)

# ===========================
# 🧠 Load trained model
# ===========================
MODEL_PATH = "model/flood_model.pkl"

if not os.path.exists(MODEL_PATH):
    st.warning("⚠️ Model not found! Training a new model...")
    train_model()
    
with open(MODEL_PATH, "rb") as file:
    model = pickle.load(file)

# ===========================
# 🌦 Streamlit UI
# ===========================
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="centered")
st.title("🌊 FloodGuard AI - Flood Prediction System")

st.write("এই অ্যাপটি রিয়েল-টাইম আবহাওয়া ও নদীর তথ্য বিশ্লেষণ করে বন্যার ঝুঁকি অনুমান করে।")

# ---------------------------
# 🧩 User Inputs
# ---------------------------
st.sidebar.header("📥 Input Parameters")

rainfall = st.sidebar.number_input("Rainfall (mm)", min_value=0.0, max_value=500.0, step=1.0)
temperature = st.sidebar.number_input("Temperature (°C)", min_value=0.0, max_value=50.0, step=0.5)
humidity = st.sidebar.number_input("Humidity (%)", min_value=0.0, max_value=100.0, step=1.0)
river_level = st.sidebar.number_input("River Level (m)", min_value=0.0, max_value=20.0, step=0.1)

# ---------------------------
# 🔍 Prediction
# ---------------------------
if st.button("🔮 Predict Flood Risk"):
    input_data = pd.DataFrame([[rainfall, temperature, humidity, river_level]],
                              columns=["rainfall", "temperature", "humidity", "river_level"])
    prediction = model.predict(input_data)[0]
    if prediction == 1:
        st.error("🚨 High Risk: Flood likely to occur!")
    else:
        st.success("✅ Low Risk: No flood expected.")

# ---------------------------
# 📊 Optional: Show live data
# ---------------------------
if st.checkbox("Show Live Weather & River Data"):
    st.subheader("🌦 Current Weather Data")
    try:
        weather = get_weather_data()
        st.json(weather)
    except Exception as e:
        st.warning(f"Weather API not available: {e}")

    st.subheader("🌊 River Data")
    try:
        river = get_river_data()
        st.json(river)
    except Exception as e:
        st.warning(f"River API not available: {e}")

st.caption("Developed by Zahid Hasan 💻 | Powered by Streamlit")
