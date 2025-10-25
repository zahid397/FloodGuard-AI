# 🌊 FloodGuard AI - Auto Train + Gemini 2.5 + Bengali Voice
# Developed by Zahid Hasan 💻

import streamlit as st
import pandas as pd
import numpy as np
import os, pickle, requests, base64
from io import BytesIO
from gtts import gTTS
import google.generativeai as genai
from sklearn.ensemble import RandomForestClassifier

# ====================== PAGE CONFIG ======================
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")
st.title("🌊 FloodGuard AI - 2025 Edition")
st.caption("💻 Developed by Zahid Hasan | Gemini 2.5 + Bengali Voice + Auto-Train Flood Model")

# ====================== MODEL SETUP ======================
MODEL_PATH = "model/flood_model.pkl"
os.makedirs("model", exist_ok=True)

def train_flood_model():
    """Train a simple model if not found."""
    data = pd.DataFrame({
        "rainfall_mm": np.random.uniform(0, 400, 1000),
        "temperature_c": np.random.uniform(15, 38, 1000),
        "humidity_percent": np.random.uniform(40, 95, 1000),
        "water_level_m": np.random.uniform(0, 10, 1000)
    })
    data["flood_risk"] = (
        (data["rainfall_mm"] > 200) |
        (data["water_level_m"] > 6) |
        ((data["humidity_percent"] > 85) & (data["temperature_c"] < 25))
    ).astype(int)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(data[["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"]], data["flood_risk"])
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    return model

if not os.path.exists(MODEL_PATH):
    st.warning("⚠️ Flood model not found. Training new one automatically...")
    model = train_flood_model()
else:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    st.success("✅ Flood model loaded successfully!")

# ====================== WEATHER DATA ======================
def get_weather(city="Dhaka"):
    api_key = st.secrets.get("OPENWEATHER_API") or os.getenv("OPENWEATHER_API")
    if not api_key:
        return {"city": city, "temp": "29°C", "humidity": "80%", "desc": "Clear sky (Demo Mode)"}
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url)
        d = r.json()
        if r.status_code == 200:
            return {
                "city": d.get("name", city),
                "temp": f"{d['main']['temp']} °C",
                "humidity": f"{d['main']['humidity']}%",
                "desc": d['weather'][0]['description'].capitalize()
            }
        else:
            return {"city": city, "temp": "30°C", "humidity": "85%", "desc": "Demo weather data"}
    except Exception as e:
        return {"error": str(e)}

# ====================== GEMINI SETUP ======================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    genai = None
    st.warning("⚠️ Gemini API key not found in Streamlit Secrets!")

# ====================== INPUTS ======================
st.sidebar.header("📥 Input Parameters")
rain = st.sidebar.slider("Rainfall (mm)", 0.0, 400.0, 120.0)
temp = st.sidebar.slider("Temperature (°C)", 0.0, 45.0, 28.0)
hum = st.sidebar.slider("Humidity (%)", 0.0, 100.0, 80.0)
river = st.sidebar.slider("River Level (m)", 0.0, 10.0, 5.0)

# ====================== PREDICTION ======================
if st.button("🔮 Predict Flood Risk"):
    X = pd.DataFrame([[rain, temp, hum, river]], columns=["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"])
    pred = model.predict(X)[0]
    risk = "⚠️ High Risk" if pred == 1 else "✅ Safe Zone"
    color = "red" if pred == 1 else "green"
    st.markdown(f"### **Flood Risk:** <span style='color:{color}'>{risk}</span>", unsafe_allow_html=True)

# ====================== LIVE DATA ======================
st.divider()
st.subheader("📡 Live Weather & River Data")
weather = get_weather("Dhaka")
st.json(weather)
st.json({
    "Padma": {"level_m": 5.6, "status": "Rising"},
    "Jamuna": {"level_m": 6.2, "status": "Stable"},
    "Meghna": {"level_m": 4.1, "status": "Falling"}
})

# ====================== GEMINI CHAT ======================
st.divider()
st.subheader("💬 Ask FloodGuard AI (বাংলায় প্রশ্ন করো)")
query = st.text_input("তোমার প্রশ্ন লিখো এখানে:")

if query:
    if genai:
        try:
            model_ai = genai.GenerativeModel("gemini-2.0-flash")
            response = model_ai.generate_content(f"বাংলায় উত্তর দাও: {query}")
            answer = response.text
            st.markdown(f"**FloodGuard AI:** {answer}")

            # Voice output
            try:
                tts = gTTS(answer, lang="bn")
                buf = BytesIO()
                tts.write_to_fp(buf)
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode()
                st.markdown(
                    f'<audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
                    unsafe_allow_html=True
                )
            except:
                st.info("🎧 Voice output coming soon...")

        except Exception as e:
            st.warning(f"⚠️ Gemini response failed: {e}")
    else:
        st.info("ℹ️ Gemini AI not configured yet!")

# ====================== FOOTER ======================
st.divider()
st.caption("🌊 FloodGuard AI © 2025 | Auto-Trained Flood Model + Bengali Voice by Zahid Hasan 💻")
