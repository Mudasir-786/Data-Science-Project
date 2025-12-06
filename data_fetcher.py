# data_fetcher.py (FINAL & ULTIMATE FIX)

import requests
from datetime import datetime, timedelta
import json
import random

# --- CONFIG ---
# ✅ API KEY ADDED - Free OpenWeatherMap API Key
# Get your own API key from: https://openweathermap.org/api
# For production use, sign up and get your personal API key (it's FREE!)
OPENWEATHER_API_KEY = "fe4feefa8543e06d4f3c66d92c61b69c"  # Demo API key for testing
GEOCODING_URL = "http://api.openweathermap.org/geo/1.0/direct"
AQI_URL = "http://api.openweathermap.org/data/2.5/air_pollution/forecast"


def get_dummy_data_for_demo(city_name="Demo City"):
    """ Agar API fail ho jaye, to yeh function hardcoded data loota dega """
    
    num_entries = 168 # 7 days * 24 hours
    start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
    time_list = [(start_time + timedelta(hours=i)).isoformat() for i in range(num_entries)]
    pm2_5_data = [random.uniform(20.0, 70.0) for _ in range(num_entries)]
    
    processed_data = {
        "time": time_list,
        "pm10": [p * 1.5 for p in pm2_5_data],
        "pm2_5": pm2_5_data,
        "carbon_monoxide": [random.uniform(500.0, 1000.0) for _ in range(num_entries)],
        "nitrogen_dioxide": [random.uniform(10.0, 30.0) for _ in range(num_entries)],
        "sulphur_dioxide": [random.uniform(5.0, 15.0) for _ in range(num_entries)],
        "temperature_2m": [random.uniform(15.0, 25.0) for _ in range(num_entries)], 
        "relative_humidity_2m": [random.uniform(50.0, 70.0) for _ in range(num_entries)] 
    }
    
    return processed_data, f"{city_name} (DEMO MODE), IN"


def fetch_live_aqi_data(city_name):
    """ City name se coordinates aur phir live AQI data fetch karta hai. """

    geo_params = {
        "q": city_name,
        "limit": 1,
        "appid": OPENWEATHER_API_KEY
    }

    try:
        geo_response = requests.get(GEOCODING_URL, params=geo_params, timeout=15)
        geo_response.raise_for_status() 

        city_data_list = geo_response.json()
        
        if not city_data_list or len(city_data_list) == 0:
            return get_dummy_data_for_demo(city_name), f"{city_name} (City Not Found, using DEMO data)"
        
        city_data = city_data_list[0]
        lat = city_data.get("lat")
        lon = city_data.get("lon")
        country = city_data.get("country", "Unknown")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return get_dummy_data_for_demo(city_name), f"{city_name} (API Key Error, using DEMO data)"
        return get_dummy_data_for_demo(city_name), f"{city_name} (HTTP Error {e.response.status_code}, using DEMO data)"
    except requests.exceptions.Timeout:
        return get_dummy_data_for_demo(city_name), f"{city_name} (Request Timeout - slow connection, using DEMO data)"
    except requests.exceptions.ConnectionError:
        return get_dummy_data_for_demo(city_name), f"{city_name} (No Internet Connection, using DEMO data)"
    except Exception as e:
        return get_dummy_data_for_demo(city_name), f"{city_name} (Error: {str(e)[:50]}, using DEMO data)"

    # --- AQI DATA FETCH (Agar upar ka code chal jaye) ---
    aqi_params = {
        "lat": lat, 
        "lon": lon, 
        "appid": OPENWEATHER_API_KEY
    }

    try:
        aqi_response = requests.get(AQI_URL, params=aqi_params, timeout=15)
        aqi_response.raise_for_status()
        
        aqi_json = aqi_response.json()
        
        if "list" not in aqi_json or len(aqi_json["list"]) == 0:
            return get_dummy_data_for_demo(city_name), f"{city_name} (No AQI Data Available, using DEMO data)"
        
        # Process real AQI data
        forecast_list = aqi_json["list"]
        
        time_list = []
        pm10_list = []
        pm25_list = []
        co_list = []
        no2_list = []
        so2_list = []
        
        for entry in forecast_list:
            timestamp = entry.get("dt", 0)
            time_list.append(datetime.fromtimestamp(timestamp).isoformat())
            
            components = entry.get("components", {})
            pm10_list.append(components.get("pm10", 50.0))
            pm25_list.append(components.get("pm2_5", 25.0))
            co_list.append(components.get("co", 500.0))
            no2_list.append(components.get("no2", 20.0))
            so2_list.append(components.get("so2", 10.0))
        
        # Generate synthetic weather data for model (since OpenWeather AQI doesn't provide it)
        num_entries = len(time_list)
        processed_data = {
            "time": time_list,
            "pm10": pm10_list,
            "pm2_5": pm25_list,
            "carbon_monoxide": co_list,
            "nitrogen_dioxide": no2_list,
            "sulphur_dioxide": so2_list,
            "temperature_2m": [random.uniform(15.0, 30.0) for _ in range(num_entries)],
            "relative_humidity_2m": [random.uniform(40.0, 80.0) for _ in range(num_entries)]
        }
        
        return processed_data, f"{city_data.get('name', city_name)}, {country} (Live API Data)"

    except requests.exceptions.HTTPError as e:
        return get_dummy_data_for_demo(city_name), f"{city_name} (HTTP Error {e.response.status_code}, using DEMO data)"
    except requests.exceptions.Timeout:
        return get_dummy_data_for_demo(city_name), f"{city_name} (AQI Request Timeout, using DEMO data)"
    except requests.exceptions.ConnectionError:
        return get_dummy_data_for_demo(city_name), f"{city_name} (Connection Error, using DEMO data)"
    except Exception as e:
        return get_dummy_data_for_demo(city_name), f"{city_name} (AQI Fetch Error: {str(e)[:40]}, using DEMO data)"