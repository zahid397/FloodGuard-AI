import requests

def get_weather_data(city="Dhaka"):
    """
    Fetch current weather data from OpenWeatherMap API.
    Replace YOUR_API_KEY with a valid API key.
    """
    API_KEY = "YOUR_API_KEY"
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
