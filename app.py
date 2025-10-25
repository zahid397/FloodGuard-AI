# app.py — FloodGuard AI (Final Hackathon Version)
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

# ---- PAGE CONFIG ----
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---- THEME FIX ----
st.markdown("""
<style>
body, .stApp {
    background-color: #d9f5ff !important;
    color: #0a192f !important;
    font-family: 'Inter', sans-serif;
}
footer {visibility:hidden;}
h1, h2, h3, h4, h5, h6, p, span, label, div { color: #0a192f !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #bde6fa !important;
    border-right: 1px solid #81d4fa !important;
}
[data-testid="stSidebar"] * { color: #0a192f !important; font-weight: 500 !important; }

/* Inputs & Dropdowns */
[data-testid="stSidebar"] input, [data-testid="stSidebar"] select, [data-testid="stSidebar"] textarea {
    background-color: #ffffff !important;
    color: #0a192f !important;
    border: 1px solid #0277bd !important;
    border-radius: 6px !important;
}
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #0a192f !important;
    border-radius: 6px !important;
}

/* Buttons */
.stButton>button {
    background-color: #0277bd !important;
    color: white !important;
    border-radius: 8px;
}
.stButton>button:hover { background-color: #01579b !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] button {
    background-color: #b3e5fc !important;
    color: #0a192f !important;
}
.stTabs [aria-selected="true"] {
    background-color: #81d4fa !important;
    color: #003366 !important;
    border: 1px solid #0277bd40 !important;
}

/* Map */
.leaflet-container {
    background: #ffffff !important;
    border: 2px solid #0277bd !important;
    border-radius: 10px;
}

/* Plotly */
.js-plotly-plot text, .gtitle, .legendtext, .xtick text, .ytick text { fill: #0a192f !important; }
.plotly .modebar { background-color: #0277bd !important; color: white !important; }

/* Chat */
[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    color: #0a192f !important;
    border: 1px solid #0277bd !important;
    border-radius: 10px !important;
    font-size: 16px !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div { color: #0a192f !important; }

/* Mobile */
@media (max-width:768px){
    body{font-size:14px!important;}
    .stButton>button{font-size:15px!important;padding:8px!important;}
}
</style>
""", unsafe_allow_html=True)

# ---- HEADER ----
st.title("🌊 FloodGuard AI – Hackathon Edition 2026")
st.caption("💻 Zahid Hasan | Gemini + BWDB Mock + Voice + Heatmap + Chatbot")

# ---- SESSION ----
for k in ["risk","ai_summary","audio","messages"]:
    if k not in st.session_state:
        st.session_state[k] = "N/A" if k=="risk" else None if k in["ai_summary","audio"] else []

# ---- GEMINI ----
@st.cache_resource
def init_gemini():
    try:
        genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
        st.success("✅ Gemini 2.5 Flash model loaded")
        return model
    except:
        st.warning("⚠️ Gemini not active — demo mode only.")
        return None
gemini = init_gemini()

# ---- MOCK BWDB ----
@st.cache_data(ttl=300)
def get_bwdb():
    f=np.random.uniform(-0.5,0.5)
    return {"rivers":[
        {"name":"Padma","station":"Goalundo","level":round(8.4+f,2),"danger":10.5,"loc":[23.75,89.75]},
        {"name":"Jamuna","station":"Sirajganj","level":round(9.0+f,2),"danger":11.0,"loc":[24.45,89.70]},
        {"name":"Meghna","station":"Ashuganj","level":round(7.6+f,2),"danger":9.2,"loc":[24.02,91.00]}
    ]}

# ---- PREDICT ----
def simple_predict(r,t,h,l):
    s=(r/100)+(l/8)+(h/100)-(t/40)
    return "High" if s>2 else "Medium" if s>1 else "Low"

# ---- SIDEBAR ----
st.sidebar.header("📥 Input Parameters")
rain=st.sidebar.slider("🌧️ Rainfall (mm)",0,500,50)
temp=st.sidebar.slider("🌡️ Temperature (°C)",10,40,27)
hum=st.sidebar.slider("💧 Humidity (%)",30,100,85)
level=st.sidebar.slider("🌊 River Level (m)",0.0,20.0,5.0)
loc=st.sidebar.selectbox("📍 Location",["Dhaka","Sylhet","Rajshahi","Chittagong"])

if st.sidebar.button("🔮 Predict Flood Risk",use_container_width=True):
    st.session_state.ai_summary=None; st.session_state.audio=None
    r=simple_predict(rain,temp,hum,level)
    st.session_state.risk=r
    if gemini:
        try:
            prompt=f"Location {loc}, Rain {rain}mm, River {level}m, Hum {hum}%, Temp {temp}°C. Flood risk {r}. Give 2 short Bangla safety tips + English translation."
            res=gemini.generate_content(prompt)
            st.session_state.ai_summary=res.text[:300]
            short=res.text[:100]
            tts=gTTS(short,lang="bn"); buf=BytesIO(); tts.write_to_fp(buf)
            st.session_state.audio=buf.getvalue()
        except: pass

# ---- TABS ----
tab1,tab2,tab3,tab4=st.tabs(["🔮 Prediction","📊 Dashboard","🗺️ Map","💬 Chatbot"])

# ---- MAP TAB ----
with tab3:
    st.subheader("🗺️ Interactive Flood Risk Map")
    bwdb=get_bwdb()
    # Map focus on Bangladesh
    m=folium.Map(location=[23.7,90.3],zoom_start=7,tiles="CartoDB positron")
    folium.TileLayer(
        tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="© OpenStreetMap contributors"
    ).add_to(m)
    heat=[]
    for r in bwdb["rivers"]:
        color="red"if r["level"]>r["danger"]else"orange"if r["level"]>r["danger"]*0.9 else"green"
        folium.Marker(
            r["loc"],
            tooltip=f"{r['name']} – {r['level']} m",
            popup=f"<b>{r['name']}</b><br>Station: {r['station']}<br>Level: {r['level']}m<br>Danger: {r['danger']}m<br>Risk: {color}",
            icon=folium.Icon(color=color,icon="tint",prefix="fa")
        ).add_to(m)
        pts=70 if color=="red" else 50 if color=="orange" else 30
        heat.extend(np.random.normal(loc=r["loc"],scale=[0.5,0.5],size=(pts,2)).tolist())
    if heat:
        HeatMap(heat,radius=20,blur=15,min_opacity=0.25,
            gradient={0.2:'#4caf50',0.5:'#ff9800',0.8:'#f44336'}).add_to(m)
        st_folium(m,width="100%",height=520)
        st.success("🌍 Map rendered successfully ✅")
    else:
        st.warning("⚠️ No map data — try predicting again.")

# ---- FOOTER ----
st.divider()
st.caption("🌊 FloodGuard AI © 2026 | Gemini + NASA + BWDB | Developed by Zahid Hasan 💻")
