# app.py — FloodGuard AI (Hackathon Final)
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import google.generativeai as genai
import plotly.express as px
from gtts import gTTS
from io import BytesIO
import numpy as np
from datetime import datetime, timedelta

# ---- CONFIG ----
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---- THEME FIX (Flood-Safe) ----
st.markdown("""
<style>
body, .stApp {
    background-color: #e0f7fa !important;
    color: #0a192f !important;
    font-family: 'Inter', sans-serif;
}
footer {visibility:hidden;}
[data-testid="stSidebar"] {
    background-color: #b3e5fc !important;
    border-right: 1px solid #81d4fa !important;
}
[data-testid="stSidebar"] * {
    color: #0a192f !important;
    font-weight: 500 !important;
}
.stButton>button {
    background-color: #0277bd !important;
    color: white !important;
    border-radius: 8px;
}
.stTabs [data-baseweb="tab-list"] button {
    background-color: #b3e5fc !important;
    color: #0a192f !important;
}
.stTabs [aria-selected="true"] {
    background-color: #81d4fa !important;
    color: #003366 !important;
}
.stMetric {
    background-color: #f5f5f5 !important;
    border-radius: 10px;
}
.leaflet-container {
    background: #f5f5f5 !important;
}
.leaflet-popup-content-wrapper {
    background: white !important;
    color: #0a192f !important;
}
.plotly .modebar { background-color: #0277bd !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---- Header ----
st.title("🌊 FloodGuard AI – Hackathon Edition")
st.caption("Zahid Hasan | Gemini + BWDB Mock + Heatmap + Voice + Chat")

# ---- Session ----
for k in ["risk","ai_summary","audio","messages"]:
    if k not in st.session_state:
        st.session_state[k] = "N/A" if k=="risk" else None if k in ["ai_summary","audio"] else []

# ---- Gemini ----
@st.cache_resource
def init_gemini():
    try:
        genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))
        return genai.GenerativeModel("gemini-2.5-flash")
    except:
        return None
gemini = init_gemini()

# ---- Mock BWDB ----
@st.cache_data(ttl=300)
def get_bwdb():
    f=np.random.uniform(-0.5,0.5)
    return {"rivers":[
        {"name":"Padma","station":"Goalundo","level":round(8.4+f,2),"danger":10.5,"loc":[23.75,89.75]},
        {"name":"Jamuna","station":"Sirajganj","level":round(9.0+f,2),"danger":11.0,"loc":[24.45,89.70]},
        {"name":"Meghna","station":"Ashuganj","level":round(7.6+f,2),"danger":9.2,"loc":[24.02,91.00]}
    ]}

# ---- Predict Function ----
def simple_predict(r,t,h,l):
    s=(r/100)+(l/8)+(h/100)-(t/40)
    return "High" if s>2 else "Medium" if s>1 else "Low"

# ---- Sidebar ----
st.sidebar.header("📥 Input Parameters")
rain = st.sidebar.slider("🌧️ Rainfall (mm)",0,500,50)
temp = st.sidebar.slider("🌡️ Temperature (°C)",10,40,27)
hum = st.sidebar.slider("💧 Humidity (%)",30,100,85)
level = st.sidebar.slider("🌊 River Level (m)",0.0,20.0,5.0)
loc = st.sidebar.selectbox("📍 Location",["Dhaka","Sylhet","Rajshahi","Chittagong"])

if st.sidebar.button("🔮 Predict", use_container_width=True):
    st.session_state.ai_summary=None; st.session_state.audio=None
    r = simple_predict(rain,temp,hum,level)
    st.session_state.risk = r
    if gemini:
        try:
            prompt = f"Location {loc}, Rain {rain}mm, River {level}m, Hum {hum}%, Temp {temp}°C. Flood risk {r}. Give 2 short Bangla safety tips + English translation."
            res = gemini.generate_content(prompt)
            st.session_state.ai_summary = res.text[:300]
            short = res.text[:100]
            tts = gTTS(short, lang="bn"); buf = BytesIO(); tts.write_to_fp(buf)
            st.session_state.audio = buf.getvalue()
        except: pass

# ---- TABS ----
tab1, tab2, tab3, tab4 = st.tabs(["🔮 Prediction","📊 Dashboard","🗺️ Map","💬 Chatbot"])

# ---- Tab 1: Prediction ----
with tab1:
    st.subheader(f"📍 {loc} Flood Forecast")
    r = st.session_state.risk
    if r != "N/A":
        color = {"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"}[r]
        st.markdown(f"<h3 style='color:{color};'>🌀 {r} Flood Risk</h3>", unsafe_allow_html=True)
        if r=="High": st.error("🚨 HIGH RISK! Move to higher ground.")
        elif r=="Medium": st.warning("⚠️ Moderate risk — Stay alert.")
        else: st.success("✅ Low risk — Safe zone.")
    if st.session_state.ai_summary:
        st.markdown("### 🤖 AI Safety Tips")
        st.markdown(st.session_state.ai_summary)
    if st.session_state.audio: st.audio(st.session_state.audio, format="audio/mp3")

# ---- Tab 2: Dashboard ----
with tab2:
    st.subheader("📈 30-Day Flood Trend (Simulated)")
    bwdb = get_bwdb()
    cols = st.columns(3)
    for i, r in enumerate(bwdb["rivers"]):
        d = r["level"] - r["danger"]*0.9
        cols[i%3].metric(f"🌊 {r['name']} Level", f"{r['level']} m", delta=f"{d:+.1f} m")
    days = pd.date_range(datetime.now()-timedelta(days=29), periods=30)
    avg = np.mean([r["level"] for r in bwdb["rivers"]])
    rain_d = (avg*10)+np.random.normal(0,20,30)
    df = pd.DataFrame({"Date":days, "Rainfall (mm)":rain_d})
    df["Risk"] = df["Rainfall (mm)"].apply(lambda r: "Low" if r<60 else "Medium" if r<120 else "High")
    fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
        color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
        title="Rainfall & Flood Risk Trend")
    fig.update_layout(plot_bgcolor="#f5f5f5", paper_bgcolor="#f5f5f5")
    st.plotly_chart(fig, use_container_width=True)

# ---- Tab 3: Map ----
with tab3:
    st.subheader("🗺️ Interactive Flood Risk Map")
    bwdb = get_bwdb()
    m = folium.Map(location=[23.8,90.4], zoom_start=7, tiles="OpenStreetMap")
    # ✅ Add Stamen Terrain
    folium.TileLayer(
        tiles="https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        attr="Map tiles by Stamen Design (CC BY 3.0) | Data © OpenStreetMap"
    ).add_to(m)
    folium.LayerControl().add_to(m)
    
    heat = []
    for r in bwdb["rivers"]:
        color = "red" if r["level"] > r["danger"] else "orange" if r["level"] > r["danger"]*0.9 else "green"
        folium.Marker(
            r["loc"],
            tooltip=f"{r['name']} – {r['level']} m",
            popup=f"<b>{r['name']}</b><br>Station: {r['station']}<br>Level: {r['level']}m<br>Danger: {r['danger']}m<br>Risk: {color}",
            icon=folium.Icon(color=color, icon="tint", prefix="fa")
        ).add_to(m)
        pts = 70 if color == "red" else 50 if color == "orange" else 30
        heat.extend(np.random.normal(loc=r["loc"], scale=[0.5,0.5], size=(pts,2)).tolist())

    if heat:
        HeatMap(heat, radius=20, blur=15, min_opacity=0.25,
            gradient={0.2:'#4caf50', 0.5:'#ff9800', 0.8:'#f44336'}).add_to(m)
        st_folium(m, width="100%", height=520)
    else:
        st.warning("⚠️ No map data — try predicting again.")

# ---- Tab 4: Chatbot ----
with tab4:
    st.subheader("💬 FloodGuard AI Chat")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if q := st.chat_input("প্রশ্ন করুন / Ask a question..."):
        st.session_state.messages.append({"role":"user","content":q})
        with st.chat_message("user"): st.markdown(q)
        with st.chat_message("assistant"):
            if gemini:
                res = gemini.generate_content(
                    f"You are FloodGuard AI (Bangladesh flood expert). Answer in Bangla + English (under 100 words): {q}")
                ans = res.text
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            else:
                st.info("🔁 Demo mode only.")
    if st.button("🗑️ Clear Chat"): st.session_state.messages = []; st.rerun()

# ---- Footer ----
st.divider()
st.caption("🌊 FloodGuard AI © 2026 | Built with Streamlit + Gemini + NASA + BWDB | By Zahid Hasan 💻")
