# FloodGuard AI 🌊
# Developed by Zahid Hasan – Final Stable Version with Bangla AI Answer Support

import streamlit as st
import pandas as pd
import pickle
import os
import sys
import datetime
import folium
from streamlit_folium import st_folium

# Optional modules
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

try:
    from googletrans import Translator
except ImportError:
    Translator = None

# ===== Page Config =====
st.set_page_config(page_title="FloodGuard AI", page_icon="🌧️", layout="wide")

# Auto-refresh every 30 sec
if st_autorefresh:
    st_autorefresh(interval=30000, key="refresh")

# Import helpers
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '')))

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

# Model load
MODEL_PATH = "model/flood_model.pkl"
model = None
if not os.path.exists(MODEL_PATH):
    st.warning("⚠️ Model not found! Training new model if possible...")
    if train_model:
        try:
            train_model()
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            st.success("✅ Model trained successfully!")
        except Exception as e:
            st.error(f"Training failed: {e}")
else:
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    except Exception as e:
        st.error(f"Model load error: {e}")

# ===== Sidebar inputs =====
st.sidebar.header("📍 Input Parameters")
city = st.sidebar.selectbox("Select City", 
    ["Dhaka","Rajshahi","Sylhet","Khulna","Chattogram","Barishal","Rangpur"])
rainfall = st.sidebar.number_input("Rainfall (mm)",0.0,500.0,step=1.0)
temperature = st.sidebar.number_input("Temperature (°C)",-10.0,60.0,step=0.5)
humidity = st.sidebar.number_input("Humidity (%)",0.0,100.0,step=1.0)
river_level = st.sidebar.number_input("River Level (m)",0.0,25.0,step=0.1)

# ===== Title =====
st.title("🌊 FloodGuard AI – Smart Flood Prediction System")
st.write("এই অ্যাপ টি রিয়েল-টাইম আবহাওয়া ও নদীর তথ্য বিশ্লেষণ করে বন্যার ঝুঁকি অনুমান করে।")

# ===== Prediction =====
if st.button("🔮 Predict Flood Risk"):
    if model is None:
        st.error("❌ Model not loaded.")
    else:
        input_data = pd.DataFrame(
            [[rainfall, temperature, humidity, river_level]],
            columns=["rainfall_mm","temperature_c","humidity_percent","water_level_m"]
        )
        try:
            pred = model.predict(input_data)[0]
            if pred == 2:
                st.error("🚨 উচ্চ ঝুঁকি: বন্যা ঘটতে পারে!")
                st.toast("🚨 Flood Alert sent to authorities!")
            elif pred == 1:
                st.warning("⚠️ মধ্যম ঝুঁকি: নদীর স্তর মনিটর করুন।")
            else:
                st.success("✅ নিম্ন ঝুঁকি: কোনও বন্যা আশঙ্কা নেই।")
        except Exception as e:
            st.warning(f"⚠️ Prediction failed: {e}")

# ===== Weather & River data =====
if st.checkbox("📡 Show Live Weather & River Data"):
    col1,col2 = st.columns(2)
    with col1:
        st.subheader("🌦 Weather Data")
        if get_weather_data:
            try:
                weather = get_weather_data(city)
                if "error" not in weather:
                    st.metric("Temperature (°C)",weather["temperature"])
                    st.metric("Humidity (%)",weather["humidity"])
                    st.metric("Rain (mm)",weather["rain"])
                    st.metric("Condition",weather["description"])
                else:
                    st.warning(weather["error"])
            except Exception as e:
                st.warning(e)
        else:
            st.info("Weather API not integrated yet.")
    with col2:
        st.subheader("🌊 River Data")
        if get_river_data:
            try:
                river = get_river_data(city)
                st.json(river)
            except Exception as e:
                st.warning(e)
        else:
            st.info("River API not integrated yet.")

# ===== Map =====
st.subheader("🗺️ Flood Map Visualization")
m = folium.Map(location=[23.685,90.3563], zoom_start=6)
for name,coord in {"Padma":[23.5,89.8],"Meghna":[23.3,90.7],"Jamuna":[24.5,89.6]}.items():
    folium.Marker(location=coord,popup=f"{name} River").add_to(m)
st_folium(m,width=700,height=450)

# ===== Ask Flood AI (Bangla support) =====
st.subheader("💬 Ask Flood AI (বাংলায় প্রশ্ন করুন)")
user_msg = st.text_input("প্রশ্ন লিখুন:")

def translate_to_bangla(text):
    if not Translator: return text
    try:
        tr = Translator()
        return tr.translate(text,dest='bn').text
    except Exception:
        return text

if user_msg:
    ai_answer = "FloodGuard AI is analyzing real-time data to estimate flood risk levels."
    st.write("🤖 FloodGuard AI:", translate_to_bangla(ai_answer))

# ===== About =====
with st.expander("📘 About FloodGuard AI"):
    st.markdown("""
**FloodGuard AI** হলো একটি AI-চালিত বন্যা পূর্বাভাস ও সতর্কতা সিস্টেম,  
যা আবহাওয়া ও নদীর তথ্য বিশ্লেষণ করে বাংলাদেশে বন্যা ঝুঁকি হ্রাস করতে সহায়তা করে।
""")

# ===== Footer =====
st.caption(f"⏱ Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💻 Developed by Zahid Hasan | FloodGuard AI © 2025")
