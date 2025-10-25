import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime, timedelta

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------- THEME ----------
st.markdown("""
<style>
.stApp {background-color:#e0f7fa!important;color:#0a192f!important;font-family:'Inter',sans-serif;}
.stButton>button {background-color:#0277bd!important;color:white!important;border-radius:8px;font-weight:600;}
.stButton>button:hover {background-color:#01579b!important;}
.leaflet-container {height:520px!important;border-radius:10px!important;}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Final 2026")
st.caption("💻 Zahid Hasan | BWDB Mock + Map + Smart Dashboard + Chatbot")

# ---------- STATE ----------
if "risk" not in st.session_state:
    st.session_state.risk = "N/A"

# ---------- SIMPLE PREDICT ----------
def simple_predict(r, t, h, l):
    s = (r/100)+(l/8)+(h/100)-(t/40)
    return "High" if s>2 else "Medium" if s>1 else "Low"

# ---------- INPUT ----------
st.subheader("📥 Input Parameters")
col1, col2 = st.columns(2)
with col1:
    rain = st.slider("🌧️ Rainfall (mm)", 0, 500, 120)
    temp = st.slider("🌡️ Temperature (°C)", 10, 40, 28)
with col2:
    hum = st.slider("💧 Humidity (%)", 30, 100, 80)
    level = st.slider("🌊 River Level (m)", 0.0, 20.0, 6.5)

loc = st.selectbox("📍 Location", ["Dhaka","Sylhet","Rajshahi","Chittagong"])
predict_btn = st.button("🔮 Predict Flood Risk", use_container_width=True)

# ---------- PREDICT ----------
if predict_btn or st.session_state.risk != "N/A":
    st.session_state.risk = simple_predict(rain, temp, hum, level)
    r = st.session_state.risk
    color_map = {"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"}
    color = color_map[r]
    st.markdown(f"<h3 style='color:{color};text-align:center;'>🌀 {r} Flood Risk ({loc})</h3>", unsafe_allow_html=True)

    if r=="High":
        st.error("🚨 HIGH RISK! Move to higher ground immediately.")
    elif r=="Medium":
        st.warning("⚠️ Moderate risk — Stay alert.")
    else:
        st.success("✅ Low risk — Safe conditions.")

    # ---------- DASHBOARD ----------
    st.subheader("📊 30-Day Rainfall & Risk Trend")
    days = pd.date_range(datetime.now()-timedelta(days=29), periods=30)
    rain_data = np.clip(50+30*np.sin(np.linspace(0,3,30))+np.random.normal(0,10,30),0,200)
    risk = ["Low" if x<60 else "Medium" if x<120 else "High" for x in rain_data]
    df = pd.DataFrame({"Date":days,"Rainfall (mm)":rain_data,"Risk":risk})
    fig = plotly.express.line(df,x="Date",y="Rainfall (mm)",color="Risk",
        color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
        title="Rainfall & Flood Risk Trend")
    st.plotly_chart(fig,use_container_width=True)

    # ---------- MAP ----------
    st.subheader("🗺️ Interactive Flood Risk Map")
    m = folium.Map(location=[23.7,90.4],zoom_start=7,tiles="CartoDB positron")
    rivers = [
        {"name":"Padma","loc":[23.75,89.75],"risk":"High"},
        {"name":"Jamuna","loc":[24.45,89.7],"risk":"Medium"},
        {"name":"Meghna","loc":[24.0,91.0],"risk":"Low"}
    ]
    heat=[]
    for rvr in rivers:
        folium.Marker(
            rvr["loc"],
            tooltip=rvr["name"],
            popup=f"{rvr['name']} – Risk: {rvr['risk']}",
            icon=folium.Icon(color={"High":"red","Medium":"orange","Low":"green"}[rvr["risk"]])
        ).add_to(m)
        heat.extend(np.random.normal(loc=rvr["loc"],scale=[0.3,0.3],size=(50,2)).tolist())
    HeatMap(heat,radius=20,blur=15,min_opacity=0.3,
            gradient={0.2:'#4caf50',0.5:'#ff9800',0.8:'#f44336'}).add_to(m)
    st_folium(m,key="map",width="100%",height=520)

else:
    st.info("👉 Use sidebar sliders & press **Predict Flood Risk** to see dashboard and map.")

# ---------- FOOTER ----------
st.divider()
st.caption("🌊 FloodGuard AI © 2026 | Developed by Zahid Hasan 💻")
