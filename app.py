# same imports
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

st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- FIXED THEME ----------
st.markdown("""
<style>
.stApp {
    background-color: #e0f7fa !important;
    color: #0a192f !important;
    font-family: "Inter", sans-serif !important;
}
footer {visibility: hidden;}
h1,h2,h3,h4,h5,h6 {color:#01579b!important;font-weight:700!important;}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#b3e5fc 0%,#e0f7fa 100%)!important;
    border-right:1px solid #81d4fa!important;
}
[data-testid="stSidebar"] * {color:#0a192f!important;font-weight:500!important;}
/* dropdown fix */
div[data-baseweb="select"]{
    background:#ffffff!important;
    color:#0a192f!important;
    border:1px solid #0288d1!important;
    border-radius:8px!important;
    box-shadow:0 2px 4px rgba(0,0,0,0.08)!important;
}
div[data-baseweb="select"]:hover{
    border:1px solid #01579b!important;
}
/* weather box fix */
.weather-box{
    background:linear-gradient(135deg,#ffffff 0%,#e1f5fe 100%);
    border:1px solid #81d4fa;
    border-radius:10px;
    padding:10px 14px;
    font-weight:600;
    box-shadow:0 2px 5px rgba(0,0,0,0.05);
    margin-bottom:10px;
}
.stButton>button{
    background:#0277bd!important;
    color:white!important;
    border-radius:8px!important;
    font-weight:600!important;
    border:none!important;
    transition:all 0.2s ease;
}
.stButton>button:hover{background:#01579b!important;transform:scale(1.02)!important;}
[data-testid="stChatInput"] textarea{
    background:#ffffff!important;
    color:#0a192f!important;
    border:1px solid #0277bd!important;
    border-radius:10px!important;
}
[data-testid="stChatMessage"] p,[data-testid="stChatMessage"] div{
    color:#0a192f!important;
}
.js-plotly-plot .plotly{
    background:#ffffff!important;
    border-radius:10px!important;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Final 2026")
st.caption("💻 Zahid Hasan | Gemini Flash + BWDB Mock + Map + Chatbot + Voice Alerts")

# ---------- GEMINI ----------
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if key:
            genai.configure(api_key=key)
            m = genai.GenerativeModel("gemini-2.5-flash")
            st.success("✅ Gemini 2.5 Flash Connected")
            return m
    except Exception as e:
        st.warning(f"Gemini setup failed: {e}")
    return None

gemini = init_gemini()

# ---------- MOCK + SIDEBAR ----------
@st.cache_data(ttl=300)
def get_bwdb():
    f = np.random.uniform(-0.5,0.5)
    return [
        {"River":"Padma","Station":"Goalundo","Level (m)":8.5+f,"Danger (m)":10.5},
        {"River":"Jamuna","Station":"Sirajganj","Level (m)":9.1+f,"Danger (m)":11.0},
        {"River":"Meghna","Station":"Ashuganj","Level (m)":7.6+f,"Danger (m)":9.2},
    ]

def predict_flood(r,t,h,l):
    s=(r/100)+(l/8)+(h/100)-(t/40)
    return "High" if s>2 else "Medium" if s>1 else "Low"

st.sidebar.header("📥 Flood Risk Inputs")
rain=st.sidebar.slider("🌧️ Rainfall (mm)",0,500,50)
temp=st.sidebar.slider("🌡️ Temperature (°C)",10,40,27)
hum=st.sidebar.slider("💧 Humidity (%)",30,100,85)
level=st.sidebar.slider("🌊 River Level (m)",0.0,20.0,5.0)
loc=st.sidebar.selectbox("📍 Location",["Dhaka","Sylhet","Rajshahi","Chittagong"])

if st.sidebar.button("🔮 Predict Flood Risk",use_container_width=True):
    st.session_state.risk=predict_flood(rain,temp,hum,level)
    if gemini:
        res=gemini.generate_content(
            f"{loc} flood forecast. Rain={rain}, River={level}, Hum={hum}, Temp={temp}. Give 2 Bangla tips."
        )
        st.session_state.ai_summary=res.text
        tts=gTTS(res.text.split("\n")[0][:80],lang="bn")
        buf=BytesIO();tts.write_to_fp(buf);st.session_state.audio=buf.getvalue()

# ---------- WEATHER ----------
st.subheader("☁️ Daily Weather & Rainfall Report (OpenWeather)")
st.markdown("<div class='weather-box'>🌤️ Haze | 🌡️ 25.9°C | 💧 83% | 🌧️ 0mm/h | 💨 0m/s</div>", unsafe_allow_html=True)

# ---------- RIVER ----------
st.subheader("🌊 River Status Board (Live Simulation)")
df=pd.DataFrame(get_bwdb())
df["Risk"]=np.where(df["Level (m)"]>df["Danger (m)"],"High",
                    np.where(df["Level (m)"]>df["Danger (m)"]*0.9,"Medium","Low"))
st.dataframe(df,use_container_width=True,hide_index=True)

# ---------- TREND ----------
st.subheader("📊 30-Day Rainfall & Flood Risk Trend")
dates=pd.date_range(datetime.now()-timedelta(days=29),periods=30)
rain_data=np.clip(50+30*np.sin(np.linspace(0,3,30))+np.random.normal(0,10,30),0,200)
risk=["Low" if r<60 else "Medium" if r<120 else "High" for r in rain_data]
df2=pd.DataFrame({"Date":dates,"Rainfall (mm)":rain_data,"Risk":risk})
fig=px.line(df2,x="Date",y="Rainfall (mm)",color="Risk",
            color_discrete_map={"Low":"#43a047","Medium":"#fb8c00","High":"#e53935"},
            title="Rainfall vs Flood Risk Trend")
st.plotly_chart(fig,use_container_width=True)

# ---------- CHATBOT ----------
st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
for msg in st.session_state.get("messages",[]): 
    with st.chat_message(msg["role"]): st.markdown(msg["content"])
if q:=st.chat_input("Ask a question / প্রশ্ন করুন..."):
    st.session_state.messages=st.session_state.get("messages",[])
    st.session_state.messages.append({"role":"user","content":q})
    with st.chat_message("assistant"):
        if gemini:
            reply=gemini.generate_content(f"Bangladesh flood expert reply Bangla+English: {q}").text
            st.markdown(reply)
            try:
                tts=gTTS(reply.split("\n")[0][:80],lang="bn")
                buf=BytesIO();tts.write_to_fp(buf);buf.seek(0)
                st.audio(buf,format="audio/mp3")
            except: pass
        else: st.warning("Gemini key missing.")
        st.session_state.messages.append({"role":"assistant","content":reply})

st.divider()
st.caption("🌊 FloodGuard AI © 2026 | Developed by Zahid Hasan 💻")
