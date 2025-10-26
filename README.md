🌊 FloodGuard AI – Smart Flood Prediction & Awareness System

💡 Overview

FloodGuard AI is an intelligent flood risk prediction and awareness platform that combines Machine Learning (XGBoost), real-time weather data, and Google Gemini 2.5 Flash AI to forecast flood risks, generate voice safety alerts, and provide live weather visualization.

Developed as part of the InnovateX Hackathon 2025, this project aligns with UN Sustainable Development Goals (SDG 13: Climate Action & SDG 17: Partnerships for the Goals).


---

🧠 Features

✅ Flood Risk Prediction (ML)
Predict flood likelihood using rainfall, humidity, temperature, river level, and pressure data.

✅ Gemini AI Integration
Generates bilingual (Bangla + English) safety advice using Gemini 2.5 Flash.

✅ Voice Assistance
AI-generated safety alerts in Bangla via Google gTTS (Text-to-Speech).

✅ Interactive Map (Folium)
Heatmap visualization of flood-prone zones in major Bangladeshi cities.

✅ PDF Report Generator
Export personalized risk reports with location data, AI summary, and environmental conditions.

✅ Chat Assistant (Bangla + English)
Real-time AI chatbot with memory for answering flood, safety, and weather-related queries.


---

⚙️ Tech Stack

Category	Technology

Frontend	Streamlit
ML Model	XGBoost (Joblib Saved Model)
AI	Google Gemini 2.5 Flash
Speech	gTTS (Google Text-to-Speech)
Visualization	Plotly, Folium Heatmap
Data	OpenWeather API
Export	ReportLab PDF
Language	Python 3.10+



---

🧩 Installation

# Clone the repository
git clone https://github.com/yourusername/floodguard-ai.git
cd floodguard-ai

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py


---

🔑 Environment Variables

Before running, create a .env or set Streamlit secrets:

GEMINI_API_KEY = "your_google_gemini_api_key"
OPENWEATHER_API_KEY = "your_openweather_api_key"


---

📦 Folder Structure

floodguard-ai/
│
├── model/
│   └── flood_model.pkl          # Trained XGBoost model
├── app.py                       # Main Streamlit app
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
└── assets/                      # Optional (images, icons)


---

📈 How It Works

1️⃣ User inputs or fetches live weather data
2️⃣ ML model calculates flood probability
3️⃣ Gemini AI analyzes context & provides bilingual advice
4️⃣ gTTS converts advice into Bangla voice output
5️⃣ Users can download the detailed PDF report


---

🌍 Target Impact

Support early warning & disaster management systems

Enable climate-resilient policy design

Promote AI-driven environmental sustainability in Bangladesh



---

🧑‍💻 Contributors

Zahid Hasan
💼 BBA Department, Presidency University
📧 zh05698@gmail.com
🌐 ORCID: 0009-0005-ZH05698
📄 Presenter, 7th International Conference on Integrated Sciences (ICIS 2025)


---

🧾 License

This project is released under the MIT License.
Feel free to use, modify, and share with attribution.

