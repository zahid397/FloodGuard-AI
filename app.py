# 🌊 FloodGuard AI – Gemini Flash Edition 2026 (White + Readable Professional UI)
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import pickle, os
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")
st.markdown("""
<style>
body, .stApp {
    background-color: #ffffff !important;
    color: #0d1b2a !important;
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, h4, h5, h6, p, div, label, span {
    color: #0d1b2a !important;
}
footer {visibility: hidden;}

/* Tabs */
.stTabs [data-baseweb="tab-list"] button {
    background-color: #f1f5f9 !important;
    color: #0d1b2a !important;
    border-radius: 10px;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background-color: #e6f0ff !important;
    color: #003366 !important;
    font-weight: 600 !important;
    border: 1px solid #007bff40 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    color: #0d1b2a !important;
    border-right: 1px solid #e5e7eb !important;
}
[data-testid="stSidebar"] * {
    color: #0d1b2a !important;
}
.stButton>button {
    background-color: #007bff !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton>button:hover {
    background-color: #0056b3 !important;
}

/* Chat Input & Messages */
[data-testid="stChatInput"] textarea {
    background-color: #ffffff !important;
    color: #0d1b2a !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    font-size: 16px !important;
}
[data-testid="stChatInput"] label, 
[data-testid="stChatMessage"] div, 
[data-testid="stChatMessage"] p, 
[data-testid="stChatMessage"] span {
    color: #0d1b2a !important;
}
button[kind="secondaryFormSubmit"] {
    background-color: #007bff !important;
    color: white !important;
    border-radius: 6px !important;
}
button[kind="secondary"] {
    background-color: #f8fafc !important;
    color: #0d1b2a !important;
    border: 1px solid #e2e8f0 !important;
}
button[kind="secondary"]:hover {
    background-color: #e0ecff !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🌊 FloodGuard AI – Gemini Flash Edition 2026")
st.caption("💻 Zahid Hasan | Gemini 2.5/1.5 Flash + BWDB/NASA Mock + Voice + Gradient HeatMap + Smart Alerts")

# ---------- SESSION ----------
for k in ["risk", "ai_summary", "audio", "messages"]:
    if k not in st.session_state:
        st.session_state[k] = "N/A" if k == "risk" else None if k in ["ai_summary", "audio"] else []

# ---------- GEMINI ----------
@st.cache_resource
def init_gemini():
    try:
        genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            st.success("✅ Gemini 2.5 Flash model loaded")
        except Exception:
            model = genai.GenerativeModel("gemini-1.5-flash")
            st.warning("⚠️ Using Gemini 1.5 Flash (fallback)")
        return model
    except Exception as e:
        st.error(f"Gemini setup failed → {e}")
        return None
gemini = init_gemini()

# ---------- MOCK BWDB ----------
@st.cache_data(ttl=300)
def get_bwdb():
    f = np.random.uniform(-0.5, 0.5)
    return {
        "rivers": [
            {"name": "Padma", "station": "Goalundo", "level": round(8.4+f, 2), "danger": 10.5, "loc": [23.75, 89.75]},
            {"name": "Jamuna", "station": "Sirajganj", "level": round(9.0+f, 2), "danger": 11.0, "loc": [24.45, 89.70]},
            {"name": "Meghna", "station": "Ashuganj", "level": round(7.6+f, 2), "danger": 9.2, "loc": [24.02, 91.00]},
        ]
    }

# ---------- MODEL ----------
@st.cache_resource
def load_model():
    p = "model/flood_model.pkl"
    if os.path.exists(p):
        try:
            with open(p, "rb") as f: return pickle.load(f)
        except Exception as e: st.warning(f"Model load error: {e}")
    return None
model = load_model()

def simple_predict(r, t, h, l):
    s = (r/100)+(l/8)+(h/100)-(t/40)
    return "High" if s>2 else "Medium" if s>1 else "Low"

# ---------- SIDEBAR ----------
st.sidebar.header("📥 Input Parameters")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temp (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
loc = st.sidebar.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    st.session_state.ai_summary=None; st.session_state.audio=None
    try:
        if model:
            df=pd.DataFrame([[rain,temp,hum,level]],
                            columns=["rainfall_mm","temperature_c","humidity_percent","water_level_m"])
            p=model.predict(df)[0]; risk={0:"Low",1:"Medium",2:"High"}[int(p)]
        else: risk=simple_predict(rain,temp,hum,level)
        st.session_state.risk=risk
    except Exception as e:
        st.session_state.risk="Error"; st.error(f"Prediction failed {e}")
    if gemini and st.session_state.risk!="Error":
        with st.spinner("🤖 Gemini analyzing..."):
            prompt=(f"Location {loc}, Rain {rain} mm, River {level} m, Hum {hum}%, Temp {temp}°C. "
                    f"Flood risk {st.session_state.risk}. Give 2 short Bangla safety tips + English translation.")
            try:
                res=gemini.generate_content(prompt); txt=res.text[:250]
                st.session_state.ai_summary=txt
                short=txt[:100]
                try:
                    tts=gTTS(short,lang="bn"); buf=BytesIO(); tts.write_to_fp(buf)
                    st.session_state.audio=buf.getvalue()
                except: st.warning("🎧 Voice offline mode")
            except Exception as e: st.warning(f"AI summary error {e}")

# ---------- TABS ----------
tab1,tab2,tab3,tab4=st.tabs(["🔮 Prediction","📊 Dashboard","🗺️ Map","💬 Chatbot"])

# --- Prediction
with tab1:
    st.subheader(f"📍 {loc} Flood Forecast")
    r=st.session_state.risk
    if r not in ["N/A","Error"]:
        icon={"Low":"🟢","Medium":"🟡","High":"🔴"}[r]
        st.markdown(f"### {icon} **{r} Risk**")
        if r=="High": st.error("🚨 HIGH RISK! Evacuate low areas."); st.balloons()
        elif r=="Medium": st.warning("⚠️ Moderate risk – Stay alert.")
        else: st.success("✅ Low risk – Safe conditions.")
    elif r=="Error": st.error("❌ Prediction failed.")
    else: st.info("👆 Use sidebar to predict.")
    if st.session_state.ai_summary:
        st.markdown("### 🤖 AI Safety Tips"); st.markdown(st.session_state.ai_summary)
    if st.session_state.audio: st.audio(st.session_state.audio,format="audio/mp3")

# --- Dashboard
with tab2:
    st.subheader("📈 30-Day Flood Trend (Rain ↔ River Linked)")
    bwdb=get_bwdb(); cols=st.columns(3)
    for i,r in enumerate(bwdb["rivers"]):
        d=r["level"]-r["danger"]*0.9
        cols[i%3].metric(f"🌊 {r['name']} Level",f"{r['level']} m",delta=f"{d:+.1f} m",
                         delta_color="inverse" if d>0 else "normal")
    days=pd.date_range(datetime.now()-timedelta(days=29),periods=30)
    avg=np.mean([r["level"] for r in bwdb["rivers"]])
    rain_d=(avg*10)+np.random.normal(0,20,30)
    df=pd.DataFrame({"Date":days,"Rainfall (mm)":rain_d})
    df["Risk"]=df["Rainfall (mm)"].apply(lambda r:"Low"if r<60 else"Medium"if r<120 else"High")
    fig=px.line(df,x="Date",y="Rainfall (mm)",color="Risk",
        color_discrete_map={"Low":"#28a745","Medium":"#ffc107","High":"#dc3545"},
        title="Rainfall & Flood Risk Trend (Simulated)")
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig,use_container_width=True)

# --- Map
with tab3:
    st.subheader("🗺️ Interactive Flood Risk Map (Gradient Heat Zones)")
    bwdb=get_bwdb(); m=folium.Map(location=[23.8,90.4],zoom_start=7,tiles="CartoDB positron")
    heat=[]
    for r in bwdb["rivers"]:
        color="red"if r["level"]>r["danger"]else"orange"if r["level"]>r["danger"]*0.9 else"green"
        folium.Marker(r["loc"],tooltip=f"{r['name']} – {r['level']} m",
            popup=f"<b>{r['name']}</b><br>Station:{r['station']}<br>Level:{r['level']}m<br>Danger:{r['danger']}m<br>Risk:{color}",
            icon=folium.Icon(color=color,icon="tint",prefix="fa")).add_to(m)
        pts=70 if color=="red" else 50 if color=="orange" else 30
        heat.extend(np.random.normal(loc=r["loc"],scale=[0.5,0.5],size=(pts,2)).tolist())
    HeatMap(heat,radius=20,blur=15,min_opacity=0.2,max_zoom=13,
            gradient={0.2:'green',0.5:'orange',0.8:'red'}).add_to(m)
    st_folium(m,width="100%",height=500)

# --- Chatbot
with tab4:
    st.subheader("💬 FloodGuard AI Chat (Bengali + English)")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if q:=st.chat_input("প্রশ্ন করুন / Ask a question..."):
        st.session_state.messages.append({"role":"user","content":q})
        if len(st.session_state.messages)>8:
            st.session_state.messages=st.session_state.messages[-8:]
        with st.chat_message("user"): st.markdown(q)
        with st.chat_message("assistant"):
            if gemini:
                try:
                    ctx=" ".join([m['content']for m in st.session_state.messages[-3:]if m['role']=="user"])
                    res=gemini.generate_content(
                        f"You are FloodGuard AI (Bangladesh flood expert). Context:{ctx}. "
                        f"Answer in Bangla then English (<100 words): {q}")
                    ans=res.text; st.markdown(ans)
                    st.session_state.messages.append({"role":"assistant","content":ans})
                except Exception as e: st.error(f"🤖 Chat error: {e}")
            else: st.info("Demo mode: Moderate risk in Dhaka – stay alert.")
    if st.button("🗑️ Clear Chat"): st.session_state.messages=[]; st.rerun()

# ---------- FOOTER ----------
st.divider()
st.caption("🌊 FloodGuard AI © 2025-26 | Gemini 2.5/1.5 Flash + Mock BWDB/NASA | Developed by Zahid Hasan 💻 | [GitHub](https://github.com/zahid397/FloodGuard-AI)")

# ---------- NASA EXPANDER ----------
with st.expander("🛰️ NASA Flood Sim"):
    nasa_df = pd.DataFrame({
        "Basin": ["Sylhet","Barisal","Dhaka"],
        "Extent km²": [250,120,80],
        "Severity": ["High","Medium","Low"]
    })
    fig_n = px.bar(
        nasa_df, x="Basin", y="Extent km²", color="Severity",
        color_discrete_map={"High":"red","Medium":"orange","Low":"green"},
        title="NASA Flood Extent Simulation"
    )
    fig_n.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig_n, use_container_width=True)
    st.markdown("[🌐 Explore Real NASA GPM Data →](https://gpm.nasa.gov/)")
