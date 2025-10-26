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

# ---------- THEME (Dark Sidebar + Clean UI + Mobile Fix) ----------
st.markdown("""
<style>
.stApp {
    background-color: #e0f7fa !important;
    color: #0a192f !important;
    font-family: "Inter", sans-serif !important;
}
footer {visibility:hidden;}
h1,h2,h3,h4,h5,h6 {color:#0277bd!important;font-weight:700!important;}

/* Sidebar */
[data-testid="stSidebar"]{
    background-color:#0277bd!important;
    border-right:2px solid #01579b!important;
}
[data-testid="stSidebar"] * {
    color:white!important;
    font-weight:500!important;
}

/* Dropdown clean */
div[data-baseweb="select"]{
    background:#ffffff!important;
    border:1px solid #81d4fa!important;
    border-radius:8px!important;
    box-shadow:0 2px 5px rgba(0,0,0,0.08)!important;
}
div[data-baseweb="select"]:hover{
    border:1px solid #01579b!important;
}

/* Buttons */
.stButton>button{
    background:#01579b!important;
    color:white!important;
    border-radius:8px!important;
    font-weight:600!important;
    box-shadow:0 2px 4px rgba(0,0,0,0.2)!important;
    transition:all .2s ease;
}
.stButton>button:hover{
    background:#003c8f!important;
    transform:scale(1.03)!important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] button {
    background-color:#b3e5fc!important;
    color:#0a192f!important;
    border-radius:8px!important;
    border:1px solid #81d4fa!important;
}
.stTabs [aria-selected="true"] {
    background-color:#0277bd!important;
    color:white!important;
    border:1px solid #01579b!important;
}

/* Chat Input */
[data-testid="stChatInput"] textarea{
    background:#ffffff!important;
    color:#0a192f!important;
    border:1px solid #0277bd!important;
    border-radius:10px!important;
    font-size:16px!important;
}
[data-testid="stChatInput"] textarea::placeholder{color:#555!important;}
[data-testid="stChatMessage"] p,[data-testid="stChatMessage"] div{color:#0a192f!important;}

/* Plotly */
.js-plotly-plot .plotly{background:#fdfdfd!important;border-radius:10px!important;}

/* Map */
.leaflet-container{
    height:520px!important;
    border-radius:10px!important;
    box-shadow:0 4px 8px rgba(0,0,0,0.1)!important;
}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{
    background:#fff!important;
    color:#0a192f!important;
}

/* Mobile */
@media (max-width:768px){
    body{font-size:15px!important;}
    .stButton>button{font-size:15px!important;padding:8px!important;}
    h3{font-size:20px!important;}
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Final 2026")
st.caption("💻 Zahid Hasan | Gemini Flash + BWDB Mock + Map + Chatbot + Voice Alerts")

# ---------- SESSION ----------
for key in ["risk", "ai_summary", "audio", "messages"]:
    if key not in st.session_state:
        st.session_state[key] = "N/A" if key == "risk" else None if key in ["ai_summary", "audio"] else []

# ---------- GEMINI ----------
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            st.success("✅ Gemini 2.5 Flash Connected")
            return model
    except Exception as e:
        st.warning(f"Gemini setup failed: {e}")
    return None

gemini = init_gemini()

# ---------- MOCK BWDB ----------
@st.cache_data(ttl=300)
def get_bwdb():
    f = np.random.uniform(-0.5,0.5)
    return {
        "rivers":[
            {"name":"Padma","station":"Goalundo","level":round(8.4+f,2),"danger":10.5,"loc":[23.75,89.75]},
            {"name":"Jamuna","station":"Sirajganj","level":round(9.0+f,2),"danger":11.0,"loc":[24.45,89.70]},
            {"name":"Meghna","station":"Ashuganj","level":round(7.6+f,2),"danger":9.2,"loc":[24.02,91.00]},
        ]
    }

def predict_flood(r,t,h,l):
    s=(r/100)+(l/8)+(h/100)-(t/40)
    return "High" if s>2 else "Medium" if s>1 else "Low"

# ---------- SIDEBAR ----------
st.sidebar.header("📥 Flood Risk Inputs")
rain = st.sidebar.slider("🌧️ Rainfall (mm)",0,500,50)
temp = st.sidebar.slider("🌡️ Temperature (°C)",10,40,27)
hum = st.sidebar.slider("💧 Humidity (%)",30,100,85)
level = st.sidebar.slider("🌊 River Level (m)",0.0,20.0,5.0)
loc = st.sidebar.selectbox("📍 Location",["Dhaka","Sylhet","Rajshahi","Chittagong"])

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    st.session_state.risk = predict_flood(rain,temp,hum,level)
    st.session_state.ai_summary = st.session_state.audio = None
    if gemini:
        try:
            prompt = f"Location {loc}, Rain {rain}mm, River {level}m, Humidity {hum}%, Temp {temp}°C. Flood risk {st.session_state.risk}. Give 2 short Bangla safety tips + English translation."
            res = gemini.generate_content(prompt)
            txt = res.text.strip()
            st.session_state.ai_summary = txt
            tts = gTTS(txt.split("\n")[0][:80], lang="bn")
            buf = BytesIO(); tts.write_to_fp(buf)
            st.session_state.audio = buf.getvalue()
        except Exception as e:
            st.session_state.ai_summary = f"AI unavailable: {e}"

# ---------- MAIN SECTIONS ----------
st.subheader("☁️ Daily Weather & Rainfall Report (OpenWeather)")
st.markdown("<div style='background:#ffffff;border:1px solid #81d4fa;border-radius:10px;padding:10px;font-weight:600;'>🌤️ Haze | 🌡️ 25.9°C | 💧 83% | 🌧️ 0mm/h | 💨 0m/s</div>", unsafe_allow_html=True)

st.subheader("🌊 River Status Board (Live Simulation)")
rivers = get_bwdb()["rivers"]
df = pd.DataFrame(rivers)
df["Risk"] = np.where(df["level"]>df["danger"],"High",np.where(df["level"]>df["danger"]*0.9,"Medium","Low"))
st.dataframe(df,use_container_width=True,hide_index=True)

st.subheader("📊 30-Day Rainfall & Flood Risk Trend")
days = pd.date_range(datetime.now()-timedelta(days=29), periods=30)
rainvals = np.clip(50+30*np.sin(np.linspace(0,3,30))+np.random.normal(0,10,30),0,200)
risk = ["Low" if r<60 else "Medium" if r<120 else "High" for r in rainvals]
df2 = pd.DataFrame({"Date":days,"Rainfall (mm)":rainvals,"Risk":risk})
fig = px.line(df2,x="Date",y="Rainfall (mm)",color="Risk",
    color_discrete_map={"Low":"#43a047","Medium":"#fb8c00","High":"#e53935"},
    title="Rainfall vs Flood Risk Trend")
st.plotly_chart(fig,use_container_width=True)

# ---------- CHATBOT ----------
st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
for msg in st.session_state.get("messages", []):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if q := st.chat_input("Ask a question / প্রশ্ন করুন..."):
    st.session_state.messages = st.session_state.get("messages", [])
    st.session_state.messages.append({"role":"user","content":q})
    with st.chat_message("assistant"):
        if gemini:
            reply = gemini.generate_content(f"Flood expert reply in Bangla + English: {q}").text
            st.markdown(reply)
            try:
                tts = gTTS(reply.split("\n")[0][:80], lang="bn")
                buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
                st.audio(buf, format="audio/mp3")
            except: pass
        else:
            reply = "Demo mode — Gemini API key missing."
            st.warning(reply)
        st.session_state.messages.append({"role":"assistant","content":reply})

if st.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# ---------- FOOTER ----------
st.divider()
st.caption("🌊 FloodGuard AI © 2026 | Developed by Zahid Hasan 💻 | [GitHub](https://github.com/zahid397/FloodGuard-AI)")
