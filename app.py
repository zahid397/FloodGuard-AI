# 🌊 FloodGuard AI | Gemini-Powered Smart Flood App
# Developed by Zahid Hasan 💻

import streamlit as st
import pandas as pd
import pickle
import os
import google.generativeai as genai

# ========== CONFIG ==========
st.set_page_config(page_title="FloodGuard AI", page_icon="🌧️", layout="centered")
st.title("🌊 FloodGuard AI - Smart Flood Prediction System (Gemini 2.5 Flash)")
st.caption("Developed by Zahid Hasan 💻 | Powered by Google Gemini AI ⚡")

# ========== SETUP GEMINI ==========
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ========== LOAD ML MODEL ==========
MODEL_PATH = "model/flood_model.pkl"
model = None

if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
else:
    st.warning("⚠️ Flood prediction model not found! Please train it first.")

# ========== SIDEBAR INPUT ==========
st.sidebar.header("📥 Input Parameters")
rainfall = st.sidebar.number_input("Rainfall (mm)", min_value=0.0, max_value=500.0, step=1.0)
temperature = st.sidebar.number_input("Temperature (°C)", min_value=-10.0, max_value=60.0, step=0.5)
humidity = st.sidebar.number_input("Humidity (%)", min_value=0.0, max_value=100.0, step=1.0)
water_level = st.sidebar.number_input("River Level (m)", min_value=0.0, max_value=25.0, step=0.1)

# ========== FLOOD PREDICTION ==========
if st.button("🔮 Predict Flood Risk"):
    if model is None:
        st.error("❌ Model not loaded. Train or upload a valid model first.")
    else:
        input_data = pd.DataFrame([[rainfall, temperature, humidity, water_level]],
                                  columns=["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"])
        try:
            pred = model.predict(input_data)[0]
            if pred == 2 or pred == "high":
                st.error("🚨 High Flood Risk! Evacuate low areas immediately.")
            elif pred == 1 or pred == "medium":
                st.warning("⚠️ Medium Risk: Stay alert and monitor updates.")
            else:
                st.success("✅ Low Risk: No immediate flood concern.")
        except Exception as e:
            st.warning(f"⚠️ Prediction failed: {e}")

# ========== GEMINI CHATBOT (ASK FLOOD AI) ==========
st.divider()
st.subheader("💬 Ask FloodGuard AI (বাংলা বা ইংরেজি)")

def ask_flood_ai(question):
    """Send a user question to Gemini 2.5 Flash and return AI answer."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = f"You are FloodGuard AI, an assistant for flood prediction in Bangladesh. Answer in Bangla. প্রশ্ন: {question}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Error fetching AI response: {e}"

user_msg = st.text_input("তোমার প্রশ্ন লিখো এখানে:")

if user_msg:
    with st.spinner("🤖 FloodGuard AI ভাবছে..."):
        answer = ask_flood_ai(user_msg)
        st.markdown(f"**FloodGuard AI:** {answer}")

# ========== FUTURE FEATURES ==========
st.divider()
st.markdown("""
### 🔮 Upcoming Features
- 📡 Live Weather & River Data (Padma, Jamuna, Meghna)
- 🗺️ Flood Map Visualization (Google Maps + Folium)
- 📊 Flood Risk History Dashboard
- 🔔 Smart Alert Notifications (SMS / Email)
- 🧠 City-Sector Flood Forecast Cards
- 🧍‍♂️ Bengali Voice Chat Support (Text-to-Speech)
""")
