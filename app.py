# app.py - FloodGuard AI (stable mobile-friendly)
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

# ---------- THEME / CSS FIXES (selectbox + sidebar color + mobile) ----------
st.markdown("""
<style>
/* app background + fonts */
.stApp { background-color: #eaf8fb !important; color: #072033 !important; font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; }

/* sidebar background + inputs */
[data-testid="stSidebar"] { background-color: #cfeef9 !important; color: #072033 !important; border-right: 1px solid rgba(2,119,189,0.15) !important; }
[data-testid="stSidebar"] label, [data-testid="stSidebar"] div, [data-testid="stSidebar"] p { color: #072033 !important; }

/* selectbox / dropdown background fix (mobile friendly) */
div[data-baseweb="select"], div[data-baseweb="select"] > div, .stSelectbox [role="button"] {
  background-color: #ffffff !important;
  color: #072033 !important;
  border-radius: 8px !important;
}

/* buttons */
.stButton>button { background-color: #0277bd !important; color: white !important; border-radius: 8px !important; font-weight:600 !important; }
.stButton>button:hover { background-color: #01579b !important; }

/* map container (force height so mobile shows) */
.leaflet-container { height: 520px !important; border-radius: 12px !important; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }

/* chat input styling */
[data-testid="stChatInput"] textarea { background: #fff !important; color: #072033 !important; border-radius: 8px !important; }

/* headings */
h1,h2,h3,h4 { color: #072033 !important; font-weight:700 !important; }

/* mobile small fixes */
@media (max-width:768px){
  body { font-size:15px !important; }
  .stButton>button { font-size:15px !important; padding:10px !important; }
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Stable 2026")
st.caption("Zahid Hasan | Gemini Flash (optional) + BWDB Mock + HeatMap + Chatbot + Voice")

# ---------- SESSION STATE ----------
if "risk" not in st.session_state:
    st.session_state.risk = "N/A"
if "ai_summary" not in st.session_state:
    st.session_state.ai_summary = None
if "audio" not in st.session_state:
    st.session_state.audio = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------- GEMINI SAFE INIT (graceful fallback) ----------
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", None)
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            return model
    except Exception as e:
        # don't crash the app on missing/invalid key
        st.warning(f"Gemini init warning: {e}")
    return None

gemini = init_gemini()

# ---------- MOCK BWDB DATA ----------
@st.cache_data(ttl=300)
def get_bwdb():
    f = np.random.uniform(-0.5, 0.5)
    return {
        "rivers":[
            {"name":"Padma","station":"Goalundo","level":round(8.4+f,2),"danger":10.5,"loc":[23.75,89.75]},
            {"name":"Jamuna","station":"Sirajganj","level":round(9.0+f,2),"danger":11.0,"loc":[24.45,89.70]},
            {"name":"Meghna","station":"Ashuganj","level":round(7.6+f,2),"danger":9.2,"loc":[24.02,91.00]}
        ]
    }

# ---------- PREDICTION FUNCTION ----------
def simple_predict(r, t, h, l):
    score = (r/100) + (l/8) + (h/100) - (t/40)
    return "High" if score > 2 else "Medium" if score > 1 else "Low"

# ---------- SIDEBAR: inputs + predict (sidebar button) ----------
st.sidebar.header("📥 Input Parameters")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
loc = st.sidebar.selectbox("📍 Location", ["Dhaka","Sylhet","Rajshahi","Chittagong"])

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    # compute risk and set session
    st.session_state.risk = simple_predict(rain, temp, hum, level)
    st.session_state.ai_summary = None
    st.session_state.audio = None

    # try generating short tips if Gemini available
    if gemini:
        try:
            prompt = f"Location {loc}, Rain {rain}mm, River {level}m, Humidity {hum}%, Temp {temp}°C. Flood risk {st.session_state.risk}. Give 2 short Bangla safety tips + English translation."
            res = gemini.generate_content(prompt)
            text = res.text.strip()
            st.session_state.ai_summary = text
            # short TTS (Bangla first line if exists)
            first = text.splitlines()[0] if text else ""
            if first:
                tts = gTTS(first, lang="bn")
                buf = BytesIO(); tts.write_to_fp(buf); st.session_state.audio = buf.getvalue()
        except Exception as e:
            st.session_state.ai_summary = f"AI unavailable ({e})"

# ---------- TABS ----------
tab1, tab2, tab3, tab4 = st.tabs(["🔮 Prediction","📊 Dashboard","🗺️ Map","💬 Chatbot"])

# --- Prediction Tab ---
with tab1:
    st.subheader(f"📍 {loc} Flood Forecast")
    if st.session_state.risk == "N/A":
        st.info("👉 Use the sidebar controls and press **Predict Flood Risk**")
    else:
        r = st.session_state.risk
        color_map = {"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"}
        st.markdown(f"<h3 style='color:{color_map[r]};'>🌀 {r} Flood Risk</h3>", unsafe_allow_html=True)
        if r == "High": st.error("🚨 HIGH RISK — Move to higher ground immediately.")
        elif r == "Medium": st.warning("⚠️ Moderate risk — Stay alert.")
        else: st.success("✅ Low risk — Safe conditions.")
    if st.session_state.ai_summary:
        st.markdown("### 🤖 AI Safety Tips")
        st.write(st.session_state.ai_summary)
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3")

# --- Dashboard Tab ---
with tab2:
    st.subheader("📈 30-Day Rainfall & Risk Trend (Simulated)")
    days = 30
    dates = pd.date_range(datetime.now() - timedelta(days=days-1), periods=days)
    rain_series = np.clip(40 + 30*np.sin(np.linspace(0,3,days)) + np.random.normal(0,10,days), 0, 220)
    risk_series = ["Low" if x<60 else "Medium" if x<120 else "High" for x in rain_series]
    df = pd.DataFrame({"Date": dates, "Rainfall (mm)": rain_series, "Risk": risk_series})
    fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
                  color_discrete_map={"Low":"#4caf50","Medium":"#ff9800","High":"#f44336"},
                  title="Rainfall & Flood Risk Trend")
    fig.update_layout(plot_bgcolor="#f7fbfc", paper_bgcolor="#f7fbfc")
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("NASA GPM (IMERG) - Real-time rainfall →"):
        st.markdown("If you want live NASA data, link here: https://gpm.nasa.gov/data/realtime")

# --- Map Tab ---
with tab3:
    st.subheader("🗺️ Interactive Flood Risk Map (Bangladesh)")
    try:
        bwdb = get_bwdb()
        m = folium.Map(location=[23.8, 90.4], zoom_start=7, tiles="CartoDB positron", attr="CartoDB")
        heat_points = []
        for r in bwdb["rivers"]:
            risk_label = "High" if r["level"] > r["danger"] else "Medium" if r["level"] > r["danger"]*0.9 else "Low"
            color = {"Low":"green","Medium":"orange","High":"red"}[risk_label]
            folium.Marker(
                location=r["loc"],
                tooltip=f"{r['name']} – {r['level']} m",
                popup=f"<b>{r['name']}</b><br>Station: {r['station']}<br>Level: {r['level']} m<br>Danger: {r['danger']} m<br>Risk: {risk_label}",
                icon=folium.Icon(color=color, icon="tint", prefix="fa")
            ).add_to(m)
            # generate clustered heat sample around station
            pts = 70 if risk_label=="High" else 50 if risk_label=="Medium" else 30
            heat_points.extend(np.random.normal(loc=r["loc"], scale=[0.3,0.3], size=(pts,2)).tolist())

        if heat_points:
            HeatMap(heat_points, radius=18, blur=12, min_opacity=0.25,
                    gradient={0.2:'#4caf50', 0.5:'#ff9800', 0.8:'#f44336'}).add_to(m)

        # pass a key to prevent flaky reloads on some mobile browsers
        st_folium(m, key="map", width="100%", height=520)

    except Exception as e:
        st.error(f"Map error: {e}")

# --- Chatbot Tab ---
with tab4:
    st.subheader("💬 FloodGuard AI Chatbot (Bangla + English)")
    # show history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if q := st.chat_input("প্রশ্ন করুন / Ask a question..."):
        st.session_state.messages.append({"role":"user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            # use gemini if available otherwise demo reply
            if gemini:
                try:
                    reply = gemini.generate_content(f"You are FloodGuard AI (Bangladesh flood expert). Answer briefly in Bangla + English: {q}").text
                except Exception as e:
                    reply = f"AI error: {e}"
            else:
                # demo reply
                reply = "Demo mode — Gemini API key missing. Example: Heavy rain → stay on higher ground. (বাংলা: বৃষ্টি বেশি হলে উঁচু জায়গায় চলে যান)।"
            st.markdown(reply)
            st.session_state.messages.append({"role":"assistant","content": reply})

        # keep history bounded
        if len(st.session_state.messages) > 20:
            st.session_state.messages = st.session_state.messages[-20:]

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ---------- FOOTER with GitHub ----------
st.divider()
st.markdown("""
🌊 **FloodGuard AI © 2026** | Developed by **Zahid Hasan** 💻  
🔗 GitHub: https://github.com/zahid397/FloodGuard-AI
""", unsafe_allow_html=True)
