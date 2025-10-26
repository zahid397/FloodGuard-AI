import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import joblib
import requests
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FloodGuard AI", page_icon="🌊", layout="wide")

# ---------------- THEME (clean select look) ----------------
st.markdown("""
<style>
.stApp{background:#fff!important;color:#0a192f!important;font-family:"Segoe UI",sans-serif!important;}
/* Sidebar */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0078d7,#0099ff)!important;border-right:3px solid #005a9e!important;
}
[data-testid="stSidebar"] *{color:#fff!important;font-weight:600!important;}
/* Clean, MS-Word-like select look */
div[role="combobox"]{
  background:#ffffff!important;border:2px solid #005a9e!important;border-radius:12px!important;
  box-shadow:0 3px 6px rgba(0,0,0,0.15)!important;padding:6px 10px!important;
}
div[role="combobox"]:hover{border-color:#004b8d!important;box-shadow:0 4px 10px rgba(0,0,0,0.25)!important;}
/* Buttons */
.stButton>button{
  background:#0078d7!important;color:#fff!important;border:none!important;border-radius:10px!important;
  font-weight:700!important;padding:8px 14px!important
}
.stButton>button:hover{background:#005a9e!important;transform:scale(1.03)}
/* Small info boxes */
.weather-box{background:#f8fbff!important;border:2px solid #0078d7!important;border-radius:10px!important;padding:10px!important;font-weight:600!important;}
.leaflet-container{height:520px!important;border-radius:10px!important;box-shadow:0 4px 8px rgba(0,0,0,0.15)!important;}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;'>🌊 FloodGuard AI – InnovateX Hackathon 2025</h1>", unsafe_allow_html=True)
st.caption("💻 Team Project | XGBoost ML | Gemini 2.5 Flash | Voice Tips | SDG 13 & 17")

# ---------------- SESSION STATE ----------------
defaults = {
    "risk": "N/A",
    "ai_summary": None,
    "audio": None,
    "weather_data": {"temp": 25.9, "hum": 83, "rain": 0},
    "prediction_inputs": None,
    "gemini_model_id": None,
    "chat_messages": []  # for chatbot
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- LOAD MODEL (silent fallback, no warning) ----------------
@st.cache_resource
def load_model():
    try:
        m = joblib.load("model/flood_model.pkl")  # keep this path exact in your repo
        st.success("✅ ML Model Loaded (XGBoost)")
        return m
    except Exception:
        return None  # silent fallback (no UI warning)

model = load_model()

# ---------------- GEMINI (robust: auto-pick available model) ----------------
@st.cache_resource
def init_gemini():
    key = None
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not key:
        key = os.getenv("GEMINI_API_KEY")
    if not key:
        st.warning("⚠️ Gemini API Key not found. Add in Secrets or environment.")
        return None, None
    try:
        genai.configure(api_key=key)
        preferred = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-001", "gemini-pro"]
        try:
            models = list(genai.list_models())
        except Exception:
            models = []
        select_id = None
        if models:
            def supports(m):
                methods = getattr(m, "supported_generation_methods", []) or []
                return any("generate" in str(x).lower() for x in methods)
            available = {m.name.split("/")[-1] for m in models if supports(m)}
            for pid in preferred:
                if pid in available:
                    select_id = pid
                    break
            if not select_id and available:
                select_id = sorted(list(available))[0]
        if not select_id:
            select_id = preferred[0]
        gmodel = genai.GenerativeModel(select_id)
        st.success(f"✅ Gemini Connected ({select_id})")
        return gmodel, select_id
    except Exception as e:
        st.error(f"Gemini init failed: {e}")
        return None, None

gemini, st.session_state.gemini_model_id = init_gemini()

# ---------------- WEATHER ----------------
def get_weather(city, api_key, slider_data):
    if not api_key:
        return slider_data["temp"], slider_data["hum"], slider_data["rain"]
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=5).json()
        if r.get("cod") == 200:
            return r["main"]["temp"], r["main"]["humidity"], r.get("rain", {}).get("1h", 0)
    except Exception:
        pass
    return slider_data["temp"], slider_data["hum"], slider_data["rain"]

# ---------------- PREDICTION ----------------
def predict_flood(features):
    if model:
        try:
            df = pd.DataFrame([features],
                              columns=["rainfall", "humidity", "temperature", "river_level", "pressure"])
            prob = model.predict_proba(df)[0][1] * 100
            risk = "High" if prob > 70 else "Medium" if prob > 30 else "Low"
            return f"{risk} ({prob:.1f}%)"
        except Exception as e:
            st.error(f"Model prediction error: {e}")
    # Rule-based fallback
    s = (features[0]/100) + (features[3]/8) + (features[1]/100) - (features[2]/40)
    risk = "High" if s > 2 else "Medium" if s > 1 else "Low"
    return f"{risk} (Rule-Based)"

# ---------------- PDF ----------------
pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
def create_pdf_report(risk, weather, summary, inputs):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("HeiseiMin-W3", 16)
    c.drawString(200, 750, "FloodGuard AI Report")
    c.setFont("HeiseiMin-W3", 12)
    c.drawString(50, 720, f"📍 Location: {inputs['loc']}")
    c.drawString(50, 700, f"Predicted Risk: {risk}")
    c.drawString(50, 680, f"Temperature: {weather['temp']:.1f}°C")
    c.drawString(50, 665, f"Humidity: {weather['hum']}%")
    c.drawString(50, 650, f"Rainfall: {weather['rain']} mm")
    c.drawString(50, 635, f"River Level: {inputs['level']} m")
    c.drawString(50, 620, f"Pressure: {inputs['pressure']} hPa")
    if summary:
        c.setFont("HeiseiMin-W3", 11)
        y = 590
        for line in summary[:600].split("\n"):
            c.drawString(60, y, line)
            y -= 15
    c.save()
    buf.seek(0)
    return buf

# ---------------- SIDEBAR ----------------
st.sidebar.header("📥 Flood Risk Inputs")
ow_key = st.sidebar.text_input("OpenWeather API Key (Optional)", type="password")
loc = st.sidebar.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])
st.sidebar.divider()
st.sidebar.markdown("#### Manual Data Overrides")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
pressure = st.sidebar.slider("💨 Pressure (hPa)", 950, 1050, 1013)

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    temp_w, hum_w, rain_w = get_weather(loc, ow_key, {"temp": temp, "hum": hum, "rain": rain})
    st.session_state.weather_data = {"temp": temp_w, "hum": hum_w, "rain": rain_w}
    st.session_state.prediction_inputs = {
        "rain": rain_w, "hum": hum_w, "temp": temp_w, "level": level, "pressure": pressure, "loc": loc
    }
    st.session_state.risk = predict_flood([rain_w, hum_w, temp_w, level, pressure])
    # clear previous AI outputs
    st.session_state.ai_summary = None
    st.session_state.audio = None
    # don't rerun here—stay on same screen so tabs are responsive

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "① Analysis", "② Weather & Rivers", "③ Map", "④ AI Safety Tips (Gemini 2.5 Flash)", "⑤ Chat Assistant"
])

with tab1:
    st.subheader("🔮 Flood Risk Analysis")
    if st.session_state.risk != "N/A":
        color = {"Low": "#43a047", "Medium": "#fb8c00", "High": "#e53935"}.get(
            st.session_state.risk.split()[0], "#0a192f")
        st.markdown(
            f"<h3>📍 {st.session_state.prediction_inputs['loc']} — Predicted Risk: "
            f"<span style='color:{color};'>{st.session_state.risk}</span></h3>", unsafe_allow_html=True
        )
        # Compact trend (simulated)
        dates = pd.date_range(datetime.now() - timedelta(days=29), periods=30)
        rain_vals = np.clip(50 + 30*np.sin(np.linspace(0, 3, 30)) + np.random.normal(0, 10, 30), 0, 200)
        risk_vals = ["Low" if rv < 60 else "Medium" if rv < 120 else "High" for rv in rain_vals]
        df_trend = pd.DataFrame({"Date": dates, "Rainfall (mm)": rain_vals, "Risk": risk_vals})
        fig = px.line(df_trend, x="Date", y="Rainfall (mm)", color="Risk",
                      color_discrete_map={"Low": "#43a047", "Medium": "#fb8c00", "High": "#e53935"},
                      title="Rainfall vs Flood Risk Trend (Simulation)")
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # PDF Download
        pdf_buffer = create_pdf_report(
            st.session_state.risk, st.session_state.weather_data,
            st.session_state.ai_summary, st.session_state.prediction_inputs
        )
        st.download_button("📄 Download Flood Report", data=pdf_buffer,
                           file_name="FloodGuard_Report.pdf", mime="application/pdf")
    else:
        st.info("⬅️ Set inputs on the left and click **Predict Flood Risk**")

with tab2:
    st.subheader("☁️ Live Weather & River Status")
    w = st.session_state.weather_data
    st.markdown(
        f"<div class='weather-box'>📍 {st.session_state.prediction_inputs['loc'] if st.session_state.prediction_inputs else 'Dhaka'}"
        f" | 🌡️ {w['temp']:.1f}°C | 💧 {w['hum']:.0f}% | 🌧️ {w['rain']:.1f}mm/h</div>",
        unsafe_allow_html=True
    )
    # River table (demo)
    rivers = [
        {"River": "Padma", "Station": "Goalundo", "Level": round(8.7 + np.random.uniform(-0.2, 0.2), 1), "Danger": 10.5},
        {"River": "Jamuna", "Station": "Sirajganj", "Level": round(9.3 + np.random.uniform(-0.2, 0.2), 1), "Danger": 11.0},
        {"River": "Meghna", "Station": "Ashugonj", "Level": round(7.8 + np.random.uniform(-0.2, 0.2), 1), "Danger": 9.2},
    ]
    df_river = pd.DataFrame(rivers)
    df_river["Risk"] = np.where(
        df_river["Level"] > df_river["Danger"], "High",
        np.where(df_river["Level"] > df_river["Danger"]*0.9, "Medium", "Low")
    )
    st.dataframe(df_river, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("🗺️ Flood Risk Heatmap (Bangladesh)")
    m = folium.Map(location=[23.8103, 90.4125], zoom_start=7, tiles="CartoDB Positron")
    intensity = max(0.05, min(1.0, (st.session_state.weather_data["rain"] or 0) / 100.0))
    HeatMap([[23.81, 90.41, intensity], [23.73, 90.40, intensity*0.8], [23.90, 90.45, intensity*0.6]],
            radius=22, blur=16, min_opacity=0.4).add_to(m)
    st_folium(m, width=750, height=480)

with tab4:
    st.subheader("🤖 AI Safety Tips — Gemini 2.5 Flash")
    st.markdown("**Selected model:** " + (st.session_state.gemini_model_id or "Not connected"))
    gen_btn = st.button("⚡ Generate Tips", use_container_width=True)

    if gen_btn:
        if not gemini:
            st.error("Gemini is not configured. Add your `GEMINI_API_KEY` first.")
        elif st.session_state.risk == "N/A" or not st.session_state.prediction_inputs:
            st.info("Please run **Predict Flood Risk** first from the sidebar.")
        else:
            with st.spinner("Generating safety tips..."):
                try:
                    p = st.session_state.prediction_inputs
                    prompt = (
                        f"Flood risk is {st.session_state.risk} for {p['loc']} "
                        f"(Rain: {p['rain']}mm, Level: {p['level']}m). "
                        "Provide exactly 2 short Bangla tips first, then 2 short English tips.\n"
                        "Format:\n"
                        "১. ...\n২. ...\n\n1. ...\n2. ..."
                    )
                    res = gemini.generate_content(prompt)
                    txt = (res.text or "").strip()
                    st.session_state.ai_summary = txt if txt else "No text returned."

                    # Bangla voice (first two Bangla lines)
                    bangla_lines = [line for line in txt.split("\n") if any('\u0980' <= ch <= '\u09FF' for ch in line)]
                    if bangla_lines:
                        speak_text = "\n".join(bangla_lines[:2])[:160]
                        tts = gTTS(speak_text, lang="bn")
                        buf = BytesIO(); tts.write_to_fp(buf); buf.seek(0)
                        st.session_state.audio = buf.getvalue()
                    else:
                        st.session_state.audio = None
                except Exception as e:
                    st.session_state.ai_summary = f"AI Error: {e}"
                    st.session_state.audio = None

    if st.session_state.ai_summary:
        st.info(st.session_state.ai_summary)
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3")

with tab5:
    st.subheader("💬 Chat Assistant (Bangla + English)")
    # show history
    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    q = st.chat_input("আপনার প্রশ্ন লিখুন / Ask anything...")
    if q:
        st.session_state.chat_messages.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)

        # build compact conversation context + risk
        context_lines = []
        if st.session_state.risk != "N/A" and st.session_state.prediction_inputs:
            p = st.session_state.prediction_inputs
            context_lines.append(
                f"Context: Current flood risk for {p['loc']} is {st.session_state.risk} "
                f"(rain {p['rain']}mm, level {p['level']}m)."
            )
        last_turns = st.session_state.chat_messages[-6:]  # last few turns
        convo_text = "\n".join([("User: " + m["content"]) if m["role"]=="user" else ("Assistant: " + m["content"])
                                for m in last_turns if m["role"] in ("user", "assistant")])

        prompt = (
            "\n".join(context_lines)
            + "\nYou are FloodGuard Chat Assistant for Bangladesh users. "
              "Answer briefly in Bangla first (1–2 lines), then in English (1–2 lines). "
              "Be practical and safety-focused.\n\n"
              + convo_text + "\nAssistant:"
        )

        with st.chat_message("assistant"):
            if not gemini:
                reply = "⚠️ Gemini is not configured. Please set GEMINI_API_KEY."
            else:
                try:
                    res = gemini.generate_content(prompt)
                    reply = (res.text or "").strip() or "Sorry, I couldn't generate a response."
                except Exception as e:
                    reply = f"AI Error: {e}"
            st.markdown(reply)
            st.session_state.chat_messages.append({"role": "assistant", "content": reply})

# ---------------- FOOTER ----------------
st.divider()
st.markdown("<p style='text-align:center;font-weight:600;'>🌊 FloodGuard AI © 2025 | Gemini 2.5 Flash | Team Project 💻</p>", unsafe_allow_html=True)
