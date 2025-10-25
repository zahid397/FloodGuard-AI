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

# ---------- THEME (আপনার থিমটি চমৎকার!) ----------
st.markdown("""
<style>
body, .stApp {
    background-color: #e0f7fa !important;
    color: #0a192f !important;
    font-family: 'Inter', sans-serif;
}
footer {visibility:hidden;}
h1, h2, h3, h4, h5, h6, p, span, label, div { color: #0a192f !important; }
[data-testid="stSidebar"] {
    background-color: #b3e5fc !important;
    border-right: 1px solid #81d4fa !important;
}
[data-testid="stSidebar"] * { color: #0a192f !important; font-weight: 500 !important; }
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
.leaflet-container {
    background: #f5f5f5 !important;
    border-radius: 12px !important;
}
.leaflet-popup-content-wrapper, .leaflet-popup-tip {
    background: #fff !important;
    color: #0a192f !important;
}
.js-plotly-plot text, .legendtext, .xtick text, .ytick text { fill: #0a192f !important; }
[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    color: #0a192f !important;
    border: 1px solid #0277bd !important;
    border-radius: 10px;
    font-size: 16px;
}
[data-testid="stChatInput"] textarea::placeholder { color: #333 !important; }
[data-testid="stChatMessage"] div, [data-testid="stChatMessage"] p { color: #0a192f !important; }
@media (max-width:768px){
    body{font-size:14px!important;}
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("🌊 FloodGuard AI – Hackathon Final 2026")
st.caption("💻 Zahid Hasan | Gemini + BWDB/NASA Mock + Voice + Map + Smart Alerts")

# ---------- SESSION STATE (উন্নত) ----------
# অ্যাপের অবস্থা মনে রাখার জন্য
if 'risk' not in st.session_state:
    st.session_state.risk = "N/A"
if 'ai_summary' not in st.session_state:
    st.session_state.ai_summary = None
if 'audio' not in st.session_state:
    st.session_state.audio = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'last_inputs' not in st.session_state:
    st.session_state.last_inputs = None

# ---------- GEMINI ----------
@st.cache_resource
def init_gemini():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # 'gemini-pro' chat-এর জন্য ভালো, 'flash' দ্রুততার জন্য ভালো।
        return genai.GenerativeModel("gemini-pro") 
    except Exception as e:
        st.error(f"⚠️ Gemini API কনফিগারেশন ব্যর্থ: {e}")
        return None
gemini = init_gemini()

# ---------- MOCK DATA ----------
@st.cache_data(ttl=300) # 5 মিনিট পর পর ডেটা রিফ্রেশ হবে
def get_bwdb():
    f = np.random.uniform(-0.5, 0.5)
    return {"rivers":[
        {"name":"Padma","station":"Goalundo","level":round(8.4+f,2),"danger":10.5,"loc":[23.75,89.75]},
        {"name":"Jamuna","station":"Sirajganj","level":round(9.0+f,2),"danger":11.0,"loc":[24.45,89.70]},
        {"name":"Meghna","station":"Ashuganj","level":round(7.6+f,2),"danger":9.2,"loc":[24.02,91.00]}
    ]}

@st.cache_data
def get_dashboard_data():
    """বাস্তবসম্মত চার্ট ডেটা তৈরি করে"""
    days = 30
    dates = pd.date_range(datetime.now() - timedelta(days=days-1), periods=days)
    # একটি সিজনাল ট্রেন্ড (sin wave) + দৈব ওঠানামা (noise)
    base_rain = 30 + 25 * np.sin(np.linspace(0, 2 * np.pi, days))
    noise = np.random.normal(0, 15, days)
    rain_data = (base_rain + noise).clip(0, 200) # 0-এর নিচে বা 200-এর উপরে যাবে না
    
    df = pd.DataFrame({"Date": dates, "Rainfall (mm)": rain_data})
    df["Risk"] = df["Rainfall (mm)"].apply(lambda r: "Low" if r < 60 else "Medium" if r < 120 else "High")
    return df

def simple_predict(r, t, h, l):
    s = (r / 100) + (l / 8) + (h / 100) - (t / 40)
    return "High" if s > 2 else "Medium" if s > 1 else "Low"

# ---------- SIDEBAR (উন্নত - নন-ব্লকিং) ----------
st.sidebar.header("📥 Input Parameters")
rain = st.sidebar.slider("🌧️ Rainfall (mm)", 0, 500, 50)
temp = st.sidebar.slider("🌡️ Temperature (°C)", 10, 40, 27)
hum = st.sidebar.slider("💧 Humidity (%)", 30, 100, 85)
level = st.sidebar.slider("🌊 River Level (m)", 0.0, 20.0, 5.0)
loc = st.sidebar.selectbox("📍 Location", ["Dhaka", "Sylhet", "Rajshahi", "Chittagong"])

if st.sidebar.button("🔮 Predict Flood Risk", use_container_width=True):
    # (FIX 1) বাটন ক্লিক করলে শুধু রিস্ক ক্যালকুলেট হয় এবং ফ্ল্যাগ সেট হয়
    # AI কল এখানে করা হয় না, তাই অ্যাপ 'freeze' হয় না
    st.session_state.risk = simple_predict(rain, temp, hum, level)
    st.session_state.last_inputs = (rain, temp, hum, level, loc) # ইনপুটগুলো মনে রাখা
    st.session_state.ai_summary = "LOADING" # AI লোডিং ফ্ল্যাগ
    st.session_state.audio = None # পুরোনো অডিও মুছে ফেলা

# ---------- TABS ----------
tab1, tab2, tab3, tab4 = st.tabs(["🔮 Prediction", "📊 Dashboard", "🗺️ Map", "💬 Chatbot"])

# --- Prediction (উন্নত - AI কল এখানে হয়) ---
with tab1:
    st.subheader(f"📍 {loc} Flood Forecast")
    
    # (FIX 1 Continued) AI জেনারেশন এখানে স্পিনারের মধ্যে হয়
    if st.session_state.ai_summary == "LOADING" and gemini:
        with st.spinner("🤖 AI is analyzing the risk..."):
            try:
                r, t, h, l, lc = st.session_state.last_inputs
                rsk = st.session_state.risk
                
                prompt = f"Location {lc}, Rain {r}mm, River {l}m, Hum {h}%, Temp {t}°C. Flood risk is {rsk}. Give 2 very short, scannable safety tips in Bangla, followed by their English translation. Format: (Bangla Tip 1)\n(Bangla Tip 2)\n\n(English Tip 1)\n(English Tip 2)"
                
                res = gemini.generate_content(prompt)
                st.session_state.ai_summary = res.text[:300] # অতিরিক্ত লম্বা টেক্সট বাদ
                
                # শুধুমাত্র বাংলা অংশটুকুর অডিও জেনারেট
                bangla_text = "\n".join(res.text.split("\n")[:2]) # প্রথম ২ লাইন (বাংলা)
                if bangla_text:
                    tts = gTTS(bangla_text, lang="bn", slow=False)
                    buf = BytesIO()
                    tts.write_to_fp(buf)
                    st.session_state.audio = buf.getvalue()
                    
            except Exception as e:
                # (FIX 3) ভুলের মেসেজ দেখানো
                st.error(f"AI বা Voice জেনারেশনে সমস্যা: {e}")
                st.session_state.ai_summary = "AI analysis failed."
                
    # রিস্ক দেখানো
    r = st.session_state.risk
    if r != "N/A":
        color = {"Low":"#4caf50", "Medium":"#ff9800", "High":"#f44336"}[r]
        st.markdown(f"<h3 style='color:{color};'>🌀 {r} Flood Risk</h3>", unsafe_allow_html=True)
        if r == "High": st.error("🚨 HIGH RISK! Evacuate low-lying areas.")
        elif r == "Medium": st.warning("⚠️ Moderate risk — stay alert.")
        else: st.success("✅ Low risk — Safe conditions.")

    # AI জেনারেটেড কন্টেন্ট দেখানো
    if st.session_state.ai_summary and st.session_state.ai_summary != "LOADING":
        st.markdown("### 🤖 AI Safety Tips")
        st.markdown(st.session_state.ai_summary)
    
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3")

# --- Dashboard (উন্নত - ক্লিনার ডেটা) ---
with tab2:
    st.subheader("📈 Live River Levels & 30-Day Trend")
    bwdb = get_bwdb()
    
    # লাইভ লেভেল (Metrics)
    cols = st.columns(len(bwdb["rivers"]))
    for i, r in enumerate(bwdb["rivers"]):
        delta_val = r["level"] - r["danger"]
        cols[i].metric(
            label=f"🌊 {r['name']} ({r['station']})",
            value=f"{r['level']} m",
            delta=f"{delta_val:+.2f} m (Danger: {r['danger']}m)",
            delta_color="inverse" # কম মানে ভালো (সবুজ), বেশি মানে খারাপ (লাল)
        )
    
    st.divider()
    
    # (FIX 4) বাস্তবসম্মত চার্ট ডেটা
    df = get_dashboard_data()
    fig = px.line(df, x="Date", y="Rainfall (mm)", color="Risk",
        color_discrete_map={"Low":"#4caf50", "Medium":"#ff9800", "High":"#f44336"},
        title="Simulated 30-Day Rainfall & Flood Risk Trend")
    fig.update_layout(plot_bgcolor="#f5f5f5", paper_bgcolor="#f5f5f5")
    st.plotly_chart(fig, use_container_width=True)

# --- Map (আপনার কোডটি ভালো ছিল) ---
with tab3:
    st.subheader("🗺️ Interactive Flood Risk Map")
    bwdb = get_bwdb()
    m = folium.Map(location=[23.7, 90.4], zoom_start=7, tiles="CartoDB positron")
    heat = []
    
    for r in bwdb["rivers"]:
        level = r["level"]
        danger = r["danger"]
        risk_text = "High" if level > danger else "Medium" if level > danger * 0.9 else "Low"
        color = {"Low": "green", "Medium": "orange", "High": "red"}[risk_text]
        
        folium.Marker(
            r["loc"],
            tooltip=f"{r['name']} – {r['level']} m",
            popup=f"<b>{r['name']}</b><br>Station: {r['station']}<br>Level: {level}m<br>Danger: {danger}m<br>Risk: {risk_text}",
            icon=folium.Icon(color=color, icon="tint", prefix="fa")
        ).add_to(m)
        
        # রিস্ক অনুযায়ী হিটম্যাপের ঘনত্ব
        pts = 70 if risk_text == "High" else 50 if risk_text == "Medium" else 30
        heat.extend(np.random.normal(loc=r["loc"], scale=[0.4, 0.4], size=(pts, 2)).tolist())
        
    if heat:
        HeatMap(heat, radius=20, blur=15, min_opacity=0.3,
                gradient={0.2:'#4caf50', 0.5:'#ff9800', 0.8:'#f44336'}).add_to(m)
    
    st_folium(m, width="100%", height=540)

# --- Chatbot (উন্নত - চ্যাট হিস্ট্রি সহ) ---
with tab4:
    st.subheader("💬 FloodGuard AI Chat (Bangla + English)")
    
    # চ্যাট হিস্ট্রি দেখানো
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): 
            st.markdown(msg["content"])
    
    if q := st.chat_input("প্রশ্ন করুন / Ask a question..."):
        # ইউজারের প্রশ্ন যোগ করা
        st.session_state.messages.append({"role":"user", "content": q})
        with st.chat_message("user"): 
            st.markdown(q)
        
        with st.chat_message("assistant"):
            if gemini:
                with st.spinner("AI ভাবছে..."):
                    try:
                        # (FIX 2) চ্যাটবটকে পুরো হিস্ট্রি পাঠানো
                        # একটি সিস্টেম প্রম্পট যোগ করা
                        system_prompt = "You are FloodGuard AI, a helpful expert on Bangladesh floods. Answer the user's latest question concisely (max 100 words), using both Bangla and English if appropriate. Use the chat history for context."
                        
                        # হিস্ট্রিকে ফরম্যাট করা
                        history_for_prompt = []
                        for m in st.session_state.messages:
                            history_for_prompt.append({"role": m["role"], "parts": [m["content"]]})
                        
                        # জেমিনি চ্যাট শুরু করা
                        chat = gemini.start_chat(history=history_for_prompt[:-1]) # শেষ প্রশ্ন বাদে সব
                        res = chat.send_message(f"{system_prompt}\n\nUSER'S NEW QUESTION: {q}")
                        
                        ans = res.text
                        st.markdown(ans)
                        st.session_state.messages.append({"role":"assistant", "content": ans})
                        
                    except Exception as e:
                        st.error(f"AI Chat Error: {e}")
            else:
                ans = "Demo mode active — no API key. (API কী ছাড়া ডেমো মোড চলছে)"
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant", "content": ans})

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ---------- FOOTER ----------
st.divider()
st.caption("🌊 FloodGuard AI © 2026 | Gemini + Mock BWDB/NASA | Developed by Zahid Hasan 💻 | [GitHub](https://github.com/zahid397/FloodGuard-AI)")
        
