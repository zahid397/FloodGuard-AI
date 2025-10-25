import os
import requests

def get_weather_data(city="Dhaka"):
    """
    Fetch current weather data from OpenWeatherMap API.
    Reads API key securely from environment variable (GitHub Secrets).
    """
    API_KEY = os.getenv("OPENWEATHER_API_KEY")  # Secret from GitHub Actions / Streamlit Secrets
    if not API_KEY:
        return {"error": "API key not found. Please set OPENWEATHER_API_KEY as a secret."}

    URL = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(URL)
        if response.status_code == 200:
            data = response.json()
            weather_info = {
                "city": data["name"],
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "rain": data.get("rain", {}).get("1h", 0),
                "description": data["weather"][0]["description"]
            }
            return weather_info
        else:
            return {"error": f"Failed to fetch weather data. Code: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
