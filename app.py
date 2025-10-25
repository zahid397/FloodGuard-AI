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

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- THEME ----------
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
[data-testid="stSidebar"] * { color: #0a192f !important; font-weight: 500 !important; }
[data-testid="stSidebar"] input, [data-testid="stSidebar"] select {
    background-color: #ffffff !important;
    color: #0a192f !important;
    border: 1px solid #0277bd !important;
}
.stButton>button {
    background-color: #0277bd !important;
    color: white !important;
    border-radius: 8px;
    font-weight: 600 !important;
}
.stButton>button:hover { background-color: #01579b !important; }
.stTabs [data-baseweb="tab-list"] button {
    background-color: #b3e5fc !important;
    color: #0a192f !important;
    border-radius: 8px;
}
.stTabs [aria-selected="true"] {
    background-color: #81d4fa !important;
    color: #003366 !important;
    border: 1px solid #0277bd40 !important;
}
.leaflet-container { background: #f5f5f5 !important; border-radius: 12px !important; }
[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    color: #0a192f !important;
    border: 1px solid #0277bd !important;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Final 2026")
st.caption("💻 Zahid Hasan | Gemini Flash + BWDB Mock + Map + Chatbot + Smart Alerts")

# ---------- SESSION ----------
for k in ["risk", "ai_summary", "audio", "messages"]:
    if k not in st.session_state:
        st.session_state[k] = "N/A" if k == "risk" else None if k in ["ai_summary", "audio"] else []

# ---------- GEMINI ----------
@st.cache_resource
def init_gemini():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel("gemini-2.5-flash")
    except:
        st.warning("⚠️ Gemini not active, demo mode only")
        return None
gemini = init_gemini()

# ---------- MOCK DATA ----------
@st.cache_data(ttl=300)
def get_bwdb():
    f = np.random.uniform(-0.5, 0.5)
    return {"rivers":[
        {"name":"Padma","station":"Goalundo","level":round(8.4+f,2),"danger":10.5,"loc":[23.75,89.75]},
        {"name":"Jamuna","station":"Sirajganj","level":round(9.0+f,2),"danger":11.0,"loc":[24.45,89.70]},
        {"name":"Meghna","station":"Ashuganj","level":round(7.6+f,2),"danger":9.2,"loc":[24.02,91.00]}
    ]}

@st.cache_data
def get_dashboard_data():
    days = 30
    dates = pd.date_range(datetime.now() - timedelta(days=days-1), periods=days)
    rain = np.clip(50 + 30*np.sin(np.linspace(0, 3, days)) + np.random.normal(0, 10, days), 0, 200)
    df = pd.DataFrame({"Date": dates, "Rainfall (mm)": rain})
    df["Risk"] = df["Rainfall (mm)"].apply(lambda r: "Low" if r<60 else "Medium" if r<120 else "High")
    return df

def simple_predict(r, t, h, l):
    s = (r / 100) + (l / 8) + (h / 100) - (t / 40)
    return "High" if s > 2 else "Medium" if s > 1 else "Low"

# ---------- SIDEBAR ----------
st.sidebar.header("📥 Input Parameters")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
loc = st.sidebar.selectbox("📍 Location", ["Dhaka","Sylhet","Rajshahi","Chittagong"])

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    st.session_state.risk = simple_predict(rain, temp, hum, level)
    if gemini:
        try:
            prompt = f"Location {loc}, Rain {rain}mm, River {level}m, Hum {hum}%, Temp {temp}°C. Flood risk {st.session_state.risk}. Give 2 short Bangla safety tips + English translation."
            res = gemini.generate_content(prompt)
            st.session_state.ai_summary = res.text[:400]
            tts = gTTS(res.text.split('\n')[0], lang="bn")
            buf = BytesIO(); tts.write_to_fp(buf)
            st.session_state.audio = buf.getvalue()
        except:
            st.session_state.ai_summary = "⚠️ AI summary unavailable."

# ---------- TABS ----------
tab1, tab2, tab3, tab4 = st.tabs(["🔮 Prediction", "📊 Dashboard", "🗺️ Map", "💬 Chatbot"])

# --- Prediction ---
with tab1:
    st.subheader(f"📍 {loc} Flood Forecast")
    color = {"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"}[st.session_state.risk]
    st.markdown(f"<h3 style='color:{color};'>🌀 {st.session_state.risk} Flood Risk</h3>", unsafe_allow_html=True)
    if st.session_state.ai_summary: st.markdown(st.session_state.ai_summary)
    if st.session_state.audio: st.audio(st.session_state.audio, format="audio/mp3")

# --- Dashboard ---
with tab2:
    st.subheader("📈 Rainfall & Flood Trend")
    df = get_dashboard_data()
    fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
        color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
        title="30-Day Rainfall & Flood Risk Trend")
    fig.update_layout(plot_bgcolor="#e0f7fa", paper_bgcolor="#e0f7fa")
    st.plotly_chart(fig, use_container_width=True)

# --- Map ---
with tab3:
    st.subheader("🗺️ Interactive Flood Risk Map (Bangladesh)")
    bwdb = get_bwdb()
    try:
        m = folium.Map(location=[23.7, 90.4], zoom_start=7, tiles="CartoDB positron")
        heat = []
        for r in bwdb["rivers"]:
            risk = "High" if r["level"] > r["danger"] else "Medium" if r["level"] > r["danger"]*0.9 else "Low"
            color = {"Low":"green","Medium":"orange","High":"red"}[risk]
            folium.Marker(
                r["loc"],
                tooltip=f"{r['name']} – {r['level']} m",
                popup=f"<b>{r['name']}</b><br>Station:{r['station']}<br>Level:{r['level']}m<br>Danger:{r['danger']}m<br>Risk:{risk}",
                icon=folium.Icon(color=color, icon="tint", prefix="fa")
            ).add_to(m)
            pts = 70 if risk == "High" else 50 if risk == "Medium" else 30
            heat.extend(np.random.normal(loc=r["loc"], scale=[0.4,0.4], size=(pts,2)).tolist())
        if heat:
            HeatMap(heat, radius=18, blur=15, min_opacity=0.25).add_to(m)
            st_folium(m, width="100%", height=540)
        else:
            raise ValueError("Empty heat data")
    except:
        st.warning("⚠️ Map failed — showing static fallback.")
        st.image("https://maps.googleapis.com/maps/api/staticmap?center=Bangladesh&zoom=6&size=800x500&maptype=terrain", caption="Fallback Google Map")

# --- Chatbot ---
with tab4:
    st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if q := st.chat_input("প্রশ্ন করুন / Ask a question..."):
        st.session_state.messages.append({"role":"user","content":q})
        with st.chat_message("assistant"):
            if gemini:
                ans = gemini.generate_content(f"You are FloodGuard AI (Bangladesh flood expert). Answer shortly (<100 words) in Bangla + English: {q}").text
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            else:
                st.info("Demo mode active.")
    if st.button("🗑️ Clear Chat"): st.session_state.messages=[]; st.rerun()

# ---------- FOOTER ----------
st.divider()
st.caption("🌊 FloodGuard AI © 2026 | Gemini Flash + BWDB Mock | Developed by Zahid Hasan 💻")
