import streamlit as st
import pandas as pd
import joblib
import numpy as np
import os

# Title
st.title("🌊 FloodGuard AI – Bangladesh Flood Risk Predictor")

# Load model
model_path = "model/flood_model.pkl"
if not os.path.exists(model_path):
    st.error("Model not found! Please run train_model.py first.")
else:
    model = joblib.load(model_path)

# Input fields
st.subheader("📥 Input Environmental Data")

rainfall = st.number_input("Rainfall (mm)", min_value=0.0, max_value=10000.0, value=200.0)
humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=80.0)
temperature = st.number_input("Temperature (°C)", min_value=0.0, max_value=50.0, value=30.0)
river_level = st.number_input("River Water Level (m)", min_value=0.0, max_value=20.0, value=5.0)
pressure = st.number_input("Atmospheric Pressure (hPa)", min_value=900.0, max_value=1100.0, value=1010.0)

# Predict button
if st.button("🔍 Predict Flood Risk"):
    data = np.array([[rainfall, humidity, temperature, river_level, pressure]])
    prediction = model.predict(data)[0]
    
    if prediction >= 0.5:
        st.error("🚨 High Flood Risk Detected!")
    else:
        st.success("✅ Low Flood Risk (Safe Zone)")

st.markdown("---")
st.caption("Developed by Zahid Hasan • Powered by AI 🌎")
