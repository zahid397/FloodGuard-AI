import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import requests
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
from streamlit_autorefresh import st_autorefresh

# ---------- AUTO REFRESH ----------
st_autorefresh(interval=3600000, key="auto_refresh")  # every 1 hour

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
.stApp{background:#e3f2fd!important;color:#0a192f!important;font-family:'Inter',sans-serif;}
[data-testid="stSidebar"]{background:#bbdefb!important;border-right:2px solid #64b5f6!important;}
[data-testid="stSidebar"] *{color:#0a192f!important;}
h1,h2,h3{color:#0a192f!important;font-weight:700!important;}
.stButton>button{background:#1565c0!important;color:white!important;border-radius:8px;font-weight:600;}
.stButton>button:hover{background:#0d47a1!important;}
[data-testid="stChatMessage"] p{color:#0a192f!important;font-weight:500;}
[data-testid="stChatMessage"]{background:#f0f9ff;border-radius:10px;padding:10px;margin-bottom:5px;}
.success-box{background:white;border-left:6px solid #4caf50;color:#1b5e20;font-weight:600;
    border-radius:6px;padding:10px;}
@media(max-width:768px){.stApp{font-size:15px!important;}.stButton>button{width:100%!important;}}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<h1 style='text-align:center;color:#0a192f;font-weight:800;margin-bottom:8px;'>
🌊 FloodGuard AI – Hackathon Pro Final 2026
</h1>
<p style='text-align:center;font-size:17px;color:#08336e;font-weight:700;
text-shadow:0 0 6px rgba(255,255,255,0.9);
background:rgba(187,222,251,0.6);border-radius:8px;padding:6px 10px;
display:inline-block;'>
💻 Zahid Hasan | Gemini 2.5 Flash ⚡ | Smart Dashboard 📊 | Weather ☁️ | River Board 🌊
</p>
""", unsafe_allow_html=True)

# ---------- SESSION ----------
for k in ["risk","ai_summary","audio","messages"]:
    if k not in st.session_state:
        st.session_state[k]="N/A" if k=="risk" else None if k in ["ai_summary","audio"] else []

# ---------- GEMINI ----------
@st.cache_resource
def init_gemini():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if not key:
            st.warning("⚠️ Gemini API Key missing — demo mode")
            return None
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        st.markdown("<div class='success-box'>✅ Gemini 2.5 Flash Connected</div>",unsafe_allow_html=True)
        return model
    except Exception as e:
        st.error(f"Gemini setup failed → {e}")
        return None

gemini = init_gemini()

# ---------- WEATHER ----------
st.subheader("☁️ Daily Weather & Rainfall Report (Live)")
try:
    key = st.secrets["OPENWEATHER_KEY"]
    loc = st.session_state.get("loc", "Dhaka")
    res = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?q={loc}&appid={key}&units=metric"
    ).json()
    desc = res["weather"][0]["description"].title()
    tempn = res["main"]["temp"]
    hum = res["main"]["humidity"]
    rain_mm = res.get("rain", {}).get("1h", 0)
    wind = res["wind"]["speed"]
    st.success(f"🌤️ {desc} | 🌡️ {tempn}°C | 💧 {hum}% | 🌧️ {rain_mm} mm/h | 💨 {wind} m/s")
except Exception as e:
    st.error(f"Weather fetch failed: {e}")

# ---------- RIVER BOARD ----------
st.subheader("🌊 River Status Board (Live Simulation)")
rivers=[
    {"name":"Padma","station":"Goalundo","level":8.7,"danger":10.5},
    {"name":"Jamuna","station":"Sirajganj","level":9.3,"danger":11.0},
    {"name":"Meghna","station":"Ashuganj","level":7.8,"danger":9.2},
]
for r in rivers:
    r["risk"]="High" if r["level"]>r["danger"] else "Medium" if r["level"]>r["danger"]*0.9 else "Low"
df = pd.DataFrame(rivers)
st.dataframe(df.rename(columns={"name":"River","station":"Station","level":"Level (m)","danger":"Danger (m)","risk":"Risk"}),
             use_container_width=True,hide_index=True)

# ---------- DASHBOARD ----------
st.subheader("📊 30-Day Rainfall & Flood Risk Trend")
dates = pd.date_range(datetime.now()-timedelta(days=29), periods=30)
rain = np.clip(50+30*np.sin(np.linspace(0,3,30))+np.random.normal(0,10,30),0,200)
risk = ["Low" if r<60 else "Medium" if r<120 else "High" for r in rain]
df = pd.DataFrame({"Date":dates,"Rainfall (mm)":rain,"Risk":risk})
fig = px.line(df,x="Date",y="Rainfall (mm)",color="Risk",
    color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
    title="Rainfall vs Flood Risk Trend")
st.plotly_chart(fig,use_container_width=True)

# ---------- CHATBOT (WITH VOICE) ----------
st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if q := st.chat_input("Ask a question / প্রশ্ন করুন..."):
    st.session_state.messages.append({"role":"user","content":q})
    with st.chat_message("user"): st.markdown(q)
    with st.chat_message("assistant"):
        if gemini:
            try:
                reply = gemini.generate_content(
                    f"You are FloodGuard AI (Bangladesh flood expert). Reply in Bangla + English: {q}"
                ).text
                st.markdown(reply)

                # 🔊 Bangla Voice Playback
                bangla = reply.split("\n")[0][:150]
                tts = gTTS(bangla, lang="bn")
                buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
                st.audio(buf, format="audio/mp3")

            except Exception as e:
                st.error(f"AI Error: {e}")
        else:
            st.markdown("Demo mode — Gemini API key missing.")
        st.session_state.messages.append({"role":"assistant","content":reply})

if st.button("🗑️ Clear Chat"): st.session_state.messages=[]; st.rerun()

# ---------- FOOTER ----------
st.divider()
st.markdown("""
🌊 **FloodGuard AI © 2026** | Developed by **Zahid Hasan** 💻  
🔗 [GitHub Repository](https://github.com/zahid397/FloodGuard-AI)
""",unsafe_allow_html=True)
