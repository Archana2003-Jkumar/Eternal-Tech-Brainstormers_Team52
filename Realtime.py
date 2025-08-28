```
import requests
import time

API_KEY = "88088888088888"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
city = "London"

def fetch_weather(city):
    url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "desc": data["weather"][0]["description"]
        }
        return weather
    else:
        print("Error:", response.status_code, response.text)
        return None

# Run in intervals
INTERVAL = 300  # seconds (5 minutes)

while True:
    weather_data = fetch_weather(city)
    if weather_data:
        print(f"[UPDATE] {city} | Temp: {weather_data['temp']}°C | "
              f"Humidity: {weather_data['humidity']}% | "
              f"Condition: {weather_data['desc']}")
        
        # 🔽 Here you can push this into your demand simulation logic
        # simulate_demand(weather_data)

    # wait before the next call
    time.sleep(INTERVAL)
```
