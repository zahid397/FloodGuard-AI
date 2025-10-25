import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
from io import BytesIO
from gtts import gTTS
import google.generativeai as genai

st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- THEME FIX ----------
st.markdown("""
<style>
body,.stApp{background-color:#e0f7fa!important;color:#00334d!important;font-family:'Inter',sans-serif;}
footer{visibility:hidden;}
h1,h2,h3,h4,h5,h6,p,span,label,div{color:#00334d!important;}
/* Sidebar */
[data-testid="stSidebar"]{background:#b3e5fc!important;border-right:1px solid #81d4fa!important;}
[data-testid="stSidebar"] *{color:#00334d!important;font-weight:500!important;}
/* Fix dark selectbox input */
.stSelectbox div[data-baseweb="select"]>div{
    background:#ffffff!important;
    color:#00334d!important;
    border:1px solid #0277bd!important;
    border-radius:8px!important;
}
/* Buttons */
.stButton>button{background:#0277bd!important;color:#fff!important;border-radius:8px;font-weight:600;}
.stButton>button:hover{background:#01579b!important;}
/* Tabs */
.stTabs [data-baseweb="tab-list"] button{background:#b3e5fc!important;color:#00334d!important;border-radius:8px;}
.stTabs [aria-selected="true"]{background:#81d4fa!important;color:#002244!important;border:1px solid #0277bd40!important;}
/* Map visible background */
.leaflet-container{background:#d9f0ff!important;border-radius:12px!important;}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:#fff!important;color:#00334d!important;}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Stable 2026")
st.caption("💻 Zahid Hasan | Gemini Flash + BWDB Mock + Voice + Map + Smart Alerts")

# ---------- SESSION ----------
for k in ["risk","ai_summary","audio","messages"]:
    if k not in st.session_state:
        st.session_state[k]="N/A" if k=="risk" else None if k in["ai_summary","audio"] else []

# ---------- MOCK DATA ----------
@st.cache_data(ttl=300)
def get_bwdb():
    f=np.random.uniform(-0.5,0.5)
    return {"rivers":[
        {"name":"Padma","station":"Goalundo","level":round(8.4+f,2),"danger":10.5,"loc":[23.75,89.75]},
        {"name":"Jamuna","station":"Sirajganj","level":round(9.0+f,2),"danger":11.0,"loc":[24.45,89.70]},
        {"name":"Meghna","station":"Ashuganj","level":round(7.6+f,2),"danger":9.2,"loc":[24.02,91.00]}
    ]}

def simple_predict(r,t,h,l):
    s=(r/100)+(l/8)+(h/100)-(t/40)
    return "High" if s>2 else "Medium" if s>1 else "Low"

# ---------- SIDEBAR ----------
st.sidebar.header("📥 Input Parameters")
rain=st.sidebar.slider("🌧️ Rainfall (mm)",0,500,50)
temp=st.sidebar.slider("🌡️ Temperature (°C)",10,40,27)
hum=st.sidebar.slider("💧 Humidity (%)",30,100,85)
level=st.sidebar.slider("🌊 River Level (m)",0.0,20.0,5.0)
loc=st.sidebar.selectbox("📍 Location",["Dhaka","Sylhet","Rajshahi","Chittagong"])
if st.sidebar.button("🔮 Predict Flood Risk",use_container_width=True):
    st.session_state.risk=simple_predict(rain,temp,hum,level)

# ---------- TABS ----------
tab1,tab2,tab3=st.tabs(["🔮 Prediction","📊 Dashboard","🗺️ Map"])

# --- Prediction ---
with tab1:
    st.subheader(f"📍 {loc} Flood Forecast")
    r=st.session_state.risk
    if r!="N/A":
        col={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"}[r]
        st.markdown(f"<h3 style='color:{col};'>🌀 {r} Flood Risk</h3>",unsafe_allow_html=True)
        st.info("✅ Safe conditions" if r=="Low" else "⚠️ Stay alert" if r=="Medium" else "🚨 High risk! Evacuate low areas")

# --- Dashboard ---
with tab2:
    st.subheader("📈 30-Day Flood Trend (Simulated)")
    df=pd.DataFrame({
        "Date":pd.date_range(datetime.now()-timedelta(days=29),periods=30),
        "Rainfall (mm)":np.random.randint(10,200,30)
    })
    df["Risk"]=df["Rainfall (mm)"].apply(lambda x:"Low"if x<60 else"Medium"if x<120 else"High")
    fig=px.line(df,x="Date",y="Rainfall (mm)",color="Risk",
        color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"})
    st.plotly_chart(fig,use_container_width=True)

# --- Map ---
with tab3:
    st.subheader("🗺️ Interactive Flood Risk Map (Bangladesh)")
    bwdb=get_bwdb()
    m=folium.Map(location=[23.7,90.4],zoom_start=7,tiles="CartoDB positron")
    heat=[]
    for r in bwdb["rivers"]:
        risk="High" if r["level"]>r["danger"] else "Medium" if r["level"]>r["danger"]*0.9 else "Low"
        color={"Low":"green","Medium":"orange","High":"red"}[risk]
        folium.Marker(
            r["loc"],
            tooltip=f"{r['name']} – {r['level']} m",
            popup=f"<b>{r['name']}</b><br>Station:{r['station']}<br>Level:{r['level']} m<br>Danger:{r['danger']} m<br>Risk:{risk}",
            icon=folium.Icon(color=color,icon="tint",prefix="fa")
        ).add_to(m)
        pts=70 if risk=="High" else 50 if risk=="Medium" else 30
        heat.extend(np.random.normal(loc=r["loc"],scale=[0.4,0.4],size=(pts,2)).tolist())
    if heat: HeatMap(heat,radius=18,blur=15,min_opacity=0.3).add_to(m)
    st_folium(m,width="100%",height=550)

st.divider()
st.caption("🌊 FloodGuard AI © 2026 | Developed by Zahid Hasan 💻")
