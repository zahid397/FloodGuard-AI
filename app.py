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
.stApp {
    background-color: #e0f7fa !important;
    color: #0a192f !important;
    font-family: "Inter", sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #b3e5fc !important;
    border-right: 1px solid #81d4fa !important;
}
.stButton>button {
    background-color: #0277bd !important;
    color: white !important;
    border-radius: 8px;
    font-weight: 600;
}
.stButton>button:hover {background-color: #01579b !important;}
.leaflet-container {
    height: 480px !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
/* Responsive for Mobile */
@media (max-width:768px){
  .stApp {font-size:15px!important;}
  h1,h2,h3 {font-size:20px!important;}
  .stButton>button{width:100%!important;font-size:15px!important;}
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Final 2026")
st.caption("💻 Zahid Hasan | BWDB Mock + Map + Smart Dashboard + Responsive Design")

# ---------- INITIALIZE ----------
if "risk" not in st.session_state: st.session_state.risk = "N/A"

# ---------- SIMPLE MODEL ----------
def predict_flood(rain, temp, hum, level):
    score = (rain/100) + (level/8) + (hum/100) - (temp/40)
    return "High" if score > 2 else "Medium" if score > 1 else "Low"

# ---------- INPUTS ----------
st.subheader("📥 Flood Risk Inputs")
col1, col2 = st.columns(2)
with col1:
    rain = st.slider("🌧️ Rainfall (mm)", 0, 500, 100)
    temp = st.slider("🌡️ Temperature (°C)", 10, 40, 28)
with col2:
    hum = st.slider("💧 Humidity (%)", 30, 100, 85)
    level = st.slider("🌊 River Level (m)", 0.0, 20.0, 6.0)
loc = st.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])
predict_btn = st.button("🔮 Predict Flood Risk", use_container_width=True)

# ---------- PREDICTION ----------
if predict_btn:
    st.session_state.risk = predict_flood(rain, temp, hum, level)

risk = st.session_state.risk
color_map = {"Low":"#4caf50", "Medium":"#ff9800", "High":"#f44336"}

if risk == "N/A":
    st.info("👉 Adjust the sliders and press Predict Flood Risk")
else:
    st.markdown(f"<h3 style='text-align:center;color:{color_map[risk]};'>🌀 {risk} Flood Risk – {loc}</h3>", unsafe_allow_html=True)
    if risk == "High":
        st.error("🚨 HIGH RISK! Move to higher ground immediately.")
    elif risk == "Medium":
        st.warning("⚠️ Moderate risk — Stay alert.")
    else:
        st.success("✅ Low risk — Safe conditions.")

# ---------- DASHBOARD ----------
st.subheader("📊 30-Day Rainfall & Risk Trend")
days = pd.date_range(datetime.now() - timedelta(days=29), periods=30)
rain_data = np.clip(50 + 30*np.sin(np.linspace(0,3,30)) + np.random.normal(0,10,30), 0, 200)
risk_data = ["Low" if x<60 else "Medium" if x<120 else "High" for x in rain_data]
df = pd.DataFrame({"Date": days, "Rainfall (mm)": rain_data, "Risk": risk_data})
fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
              color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
              title="Rainfall vs Flood Risk Trend")
fig.update_layout(margin=dict(l=10,r=10,t=40,b=10), 
                  plot_bgcolor="#f5f5f5", paper_bgcolor="#f5f5f5")
st.plotly_chart(fig, use_container_width=True)

# ---------- MAP ----------
st.subheader("🗺️ Interactive Flood Risk Map")
m = folium.Map(location=[23.7,90.4], zoom_start=7, tiles="CartoDB positron")

rivers = [
    {"name":"Padma","loc":[23.75,89.75],"risk":"High"},
    {"name":"Jamuna","loc":[24.45,89.7],"risk":"Medium"},
    {"name":"Meghna","loc":[24.0,91.0],"risk":"Low"}
]
heat_points = []
for r in rivers:
    folium.Marker(
        r["loc"], tooltip=r["name"],
        popup=f"{r['name']} – Risk: {r['risk']}",
        icon=folium.Icon(color={"High":"red","Medium":"orange","Low":"green"}[r["risk"]])
    ).add_to(m)
    heat_points.extend(np.random.normal(loc=r["loc"], scale=[0.3,0.3], size=(40,2)).tolist())
HeatMap(heat_points, radius=18, blur=12, min_opacity=0.3,
        gradient={0.2:'#4caf50',0.5:'#ff9800',0.8:'#f44336'}).add_to(m)
st_folium(m, key="map", width="100%", height=480)

# ---------- FOOTER ----------
st.divider()
st.markdown("""
🌊 **FloodGuard AI © 2026** | Developed by **Zahid Hasan** 💻  
🔗 [GitHub Repository](https://github.com/zahid397/FloodGuard-AI)
""", unsafe_allow_html=True)
