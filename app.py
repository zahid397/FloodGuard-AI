import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime, timedelta
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- THEME ----------
st.markdown("""
<style>
.stApp {
    background-color: #e3f2fd !important;
    color: #0d1b2a !important;
    font-family: "Inter", sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #bbdefb !important;
    border-right: 2px solid #64b5f6 !important;
}
[data-testid="stSidebar"] * { color: #0d1b2a !important; }
h1,h2,h3,h4,h5 { color:#0d1b2a !important;font-weight:700 !important; }
.stButton>button {
    background-color: #1565c0 !important;
    color: white !important;
    border-radius: 8px;
    font-weight: 600;
}
.stButton>button:hover { background-color: #0d47a1 !important; }
.leaflet-container {
    height: 480px !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
/* Mobile Optimization */
@media (max-width:768px){
    .stApp {font-size:15px!important;}
    h1,h2,h3{font-size:20px!important;}
    .stButton>button{width:100%!important;}
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Final 2026")
st.caption("💻 Zahid Hasan | Gemini 2.5 Flash + BWDB Mock + Map + Voice + Smart Dashboard")

# ---------- SESSION STATE ----------
if "risk" not in st.session_state: st.session_state.risk = "N/A"
if "messages" not in st.session_state: st.session_state.messages = []
if "ai_summary" not in st.session_state: st.session_state.ai_summary = None
if "audio" not in st.session_state: st.session_state.audio = None

# ---------- GEMINI INIT ----------
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.warning("⚠️ Gemini API Key missing – demo mode active")
            return None
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        st.success("✅ Gemini 2.5 Flash Connected")
        return model
    except Exception as e:
        st.error(f"Gemini setup failed → {e}")
        return None

gemini = init_gemini()

# ---------- SIMPLE PREDICT MODEL ----------
def predict_flood(rain, temp, hum, level):
    score = (rain/100) + (level/8) + (hum/100) - (temp/40)
    return "High" if score > 2 else "Medium" if score > 1 else "Low"

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("📥 Flood Risk Inputs")
    rain = st.slider("🌧️ Rainfall (mm)", 0, 500, 100)
    temp = st.slider("🌡️ Temperature (°C)", 10, 40, 28)
    hum = st.slider("💧 Humidity (%)", 30, 100, 85)
    level = st.slider("🌊 River Level (m)", 0.0, 20.0, 6.0)
    loc = st.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])
    if st.button("🔮 Predict Flood Risk", use_container_width=True):
        st.session_state.risk = predict_flood(rain, temp, hum, level)
        if gemini:
            try:
                prompt = f"Location {loc}, Rain {rain} mm, River {level} m, Humidity {hum}%, Temp {temp} °C. Flood risk {st.session_state.risk}. Give 2 short Bangla safety tips with English translation."
                res = gemini.generate_content(prompt)
                st.session_state.ai_summary = res.text
                # Short TTS
                short_text = res.text.split("\n")[0][:100]
                tts = gTTS(short_text, lang="bn")
                buf = BytesIO()
                tts.write_to_fp(buf)
                st.session_state.audio = buf.getvalue()
            except Exception as e:
                st.session_state.ai_summary = f"AI error: {e}"

# ---------- FORECAST ----------
st.subheader(f"📍 {loc} Flood Forecast")
risk = st.session_state.risk
color_map = {"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"}
if risk == "N/A":
    st.info("👉 Use sidebar to predict flood risk.")
else:
    st.markdown(f"<h3 style='color:{color_map[risk]};text-align:center;'>🌀 {risk} Flood Risk</h3>", unsafe_allow_html=True)
    if risk == "High": st.error("🚨 HIGH RISK! Move to higher ground immediately.")
    elif risk == "Medium": st.warning("⚠️ Moderate risk — Stay alert.")
    else: st.success("✅ Low risk — Safe conditions.")
if st.session_state.ai_summary:
    st.markdown("### 📋 Safety Tips")
    st.write(st.session_state.ai_summary)
if st.session_state.audio:
    st.audio(st.session_state.audio, format="audio/mp3")

# ---------- DASHBOARD ----------
st.subheader("📊 30-Day Rainfall & Flood Risk Trend")
dates = pd.date_range(datetime.now() - timedelta(days=29), periods=30)
rain_data = np.clip(50 + 30*np.sin(np.linspace(0,3,30)) + np.random.normal(0,10,30), 0, 200)
risk_data = ["Low" if r<60 else "Medium" if r<120 else "High" for r in rain_data]
df = pd.DataFrame({"Date":dates,"Rainfall (mm)":rain_data,"Risk":risk_data})
fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
              color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
              title="Rainfall vs Flood Risk")
fig.update_layout(plot_bgcolor="#f5f5f5", paper_bgcolor="#f5f5f5")
st.plotly_chart(fig, use_container_width=True)

# ---------- MAP ----------
st.subheader("🗺️ Interactive Flood Risk Map (Bangladesh)")
try:
    rivers = [
        {"name":"Padma","loc":[23.75,89.75],"risk":"High"},
        {"name":"Jamuna","loc":[24.45,89.7],"risk":"Medium"},
        {"name":"Meghna","loc":[24.0,91.0],"risk":"Low"}
    ]
    m = folium.Map(location=[23.7,90.4], zoom_start=7, tiles="CartoDB positron")
    heat_points = []
    for r in rivers:
        folium.Marker(
            r["loc"], tooltip=r["name"],
            popup=f"{r['name']} – Risk: {r['risk']}",
            icon=folium.Icon(color={"High":"red","Medium":"orange","Low":"green"}[r["risk"]])
        ).add_to(m)
        heat_points.extend(np.random.normal(loc=r["loc"], scale=[0.3,0.3], size=(50,2)).tolist())
    HeatMap(heat_points, radius=20, blur=15, min_opacity=0.3).add_to(m)
    st_folium(m, key="map", width="100%", height=480)
except Exception as e:
    st.error(f"Map error: {e}")

# ---------- CHATBOT ----------
st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
if q := st.chat_input("Ask a question / প্রশ্ন করুন..."):
    st.session_state.messages.append({"role":"user","content":q})
    with st.chat_message("user"): st.markdown(q)
    with st.chat_message("assistant"):
        if gemini:
            try:
                reply = gemini.generate_content(
                    f"You are FloodGuard AI (Bangladesh flood expert). Reply in Bangla + English: {q}"
                ).text
            except Exception as e:
                reply = f"AI error: {e}"
        else:
            reply = "Demo mode – Gemini API key missing."
        st.markdown(reply)
        st.session_state.messages.append({"role":"assistant","content":reply})
if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# ---------- FOOTER ----------
st.divider()
st.markdown("""
🌊 **FloodGuard AI © 2026** | Developed by **Zahid Hasan** 💻  
🔗 [GitHub Repository](https://github.com/zahid397/FloodGuard-AI)
""", unsafe_allow_html=True)
