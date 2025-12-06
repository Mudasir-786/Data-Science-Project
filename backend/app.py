# app.py - COMPLETE 10 MARKS PROJECT WITH ALL FEATURES
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import json
import pickle
import os
from datetime import datetime, timedelta
import sqlite3
import requests
import numpy as np
from scipy import stats
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import folium
from folium import plugins

from data_fetcher import fetch_live_aqi_data
from db_helper import get_db_connection

# Configure Flask to find templates in frontend folder
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# ============== DATABASE SETUP ==============
def init_db():
    """Initialize SQLite database for historical data"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS aqi_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  city TEXT,
                  aqi REAL,
                  pm25 REAL,
                  pm10 REAL,
                  co REAL,
                  no2 REAL,
                  so2 REAL,
                  timestamp TEXT,
                  category TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ============== HELPER FUNCTIONS ==============
def get_country_name(country_code):
    """Convert country code to full country name"""
    country_names = {
        'PK': 'Pakistan', 'IN': 'India', 'US': 'United States', 'GB': 'United Kingdom',
        'CN': 'China', 'JP': 'Japan', 'DE': 'Germany', 'FR': 'France', 'IT': 'Italy',
        'ES': 'Spain', 'CA': 'Canada', 'AU': 'Australia', 'BR': 'Brazil', 'RU': 'Russia',
        'MX': 'Mexico', 'KR': 'South Korea', 'ID': 'Indonesia', 'TR': 'Turkey', 'SA': 'Saudi Arabia',
        'AR': 'Argentina', 'PL': 'Poland', 'NL': 'Netherlands', 'BE': 'Belgium', 'SE': 'Sweden',
        'CH': 'Switzerland', 'AT': 'Austria', 'NO': 'Norway', 'DK': 'Denmark', 'FI': 'Finland',
        'IE': 'Ireland', 'PT': 'Portugal', 'GR': 'Greece', 'CZ': 'Czech Republic', 'RO': 'Romania',
        'NZ': 'New Zealand', 'SG': 'Singapore', 'MY': 'Malaysia', 'TH': 'Thailand', 'PH': 'Philippines',
        'VN': 'Vietnam', 'BD': 'Bangladesh', 'LK': 'Sri Lanka', 'NP': 'Nepal', 'AF': 'Afghanistan',
        'AE': 'United Arab Emirates', 'EG': 'Egypt', 'ZA': 'South Africa', 'NG': 'Nigeria', 'KE': 'Kenya'
    }
    return country_names.get(country_code, country_code)

def calculate_aqi_from_pm25(pm25_value):
    """EPA AQI formula for PM2.5"""
    if pm25_value <= 12.0:
        return ((50 - 0) / (12.0 - 0)) * (pm25_value - 0) + 0
    elif pm25_value <= 35.4:
        return ((100 - 51) / (35.4 - 12.1)) * (pm25_value - 12.1) + 51
    elif pm25_value <= 55.4:
        return ((150 - 101) / (55.4 - 35.5)) * (pm25_value - 35.5) + 101
    elif pm25_value <= 150.4:
        return ((200 - 151) / (150.4 - 55.5)) * (pm25_value - 55.5) + 151
    elif pm25_value <= 250.4:
        return ((300 - 201) / (250.4 - 150.5)) * (pm25_value - 150.5) + 201
    else:
        return ((500 - 301) / (500.4 - 250.5)) * (pm25_value - 250.5) + 301

def get_aqi_category(aqi_value):
    """Get AQI category with emoji - returns tuple for backward compatibility"""
    if aqi_value <= 50:
        return "Good 😊", "success"
    elif aqi_value <= 100:
        return "Moderate 😐", "warning"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups ⚠️", "warning"
    elif aqi_value <= 200:
        return "Unhealthy 😷", "danger"
    elif aqi_value <= 300:
        return "Very Unhealthy 🚨", "danger"
    else:
        return "Hazardous ☠️", "danger"

def get_aqi_category_string(aqi_value):
    """Get AQI category string only (for JSON serialization)"""
    if aqi_value <= 50:
        return "Good 😊"
    elif aqi_value <= 100:
        return "Moderate 😐"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups ⚠️"
    elif aqi_value <= 200:
        return "Unhealthy 😷"
    elif aqi_value <= 300:
        return "Very Unhealthy 🚨"
    else:
        return "Hazardous ☠️"

def get_aqi_category_with_class(aqi_value):
    """Get AQI category with Bootstrap class - same as get_aqi_category"""
    return get_aqi_category(aqi_value)

def get_health_recommendation(aqi_value):
    """Health recommendations based on AQI"""
    if aqi_value <= 50:
        return "✅ Air quality is excellent! Perfect for outdoor activities and exercise."
    elif aqi_value <= 100:
        return "😐 Air quality is acceptable. Unusually sensitive people should consider reducing prolonged outdoor exertion."
    elif aqi_value <= 150:
        return "⚠️ Unhealthy for sensitive groups. People with respiratory conditions should limit outdoor activity."
    elif aqi_value <= 200:
        return "😷 Unhealthy air! Everyone may experience health effects. Limit outdoor activities."
    elif aqi_value <= 300:
        return "🚨 Very Unhealthy! Health alert. Everyone should avoid prolonged outdoor exertion."
    else:
        return "☠️ HAZARDOUS ALERT! Stay indoors. Avoid all outdoor activities. Use air purifiers indoors."

def save_to_database(city, aqi, pm25, pm10, co, no2, so2, category):
    """Save AQI data to database"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        timestamp = datetime.now().isoformat()
        c.execute("""INSERT INTO aqi_records (city, aqi, pm25, pm10, co, no2, so2, timestamp, category) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (city, aqi, pm25, pm10, co, no2, so2, timestamp, category))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

# ============== MAIN ROUTES ==============
@app.route('/', methods=['GET', 'POST'])
def index():
    aqi_data = None
    city = "World"
    pollutants_data = {}
    chart_data = None

    if request.method == 'POST':
        city = request.form.get('city', 'Delhi')
        
        print(f"\n{'='*60}")
        print(f"🔍 Searching AQI for: {city}")
        print(f"{'='*60}")
        
        live_data_dict, status_message = fetch_live_aqi_data(city)
        
        print(f"📊 Status: {status_message}")
        print(f"📊 Data type: {type(live_data_dict)}")
        
        # Extract country from status_message (format: "City, Country (Live API Data)")
        country = "Unknown"
        country_code = "Unknown"
        city_display = city
        if ", " in status_message:
            parts = status_message.split(", ")
            if len(parts) >= 2:
                city_display = parts[0]  # Get actual city name from API
                country_part = parts[1].split(" (")[0]
                country_code = country_part
                country = get_country_name(country_code)  # Convert code to full name
        
        if isinstance(live_data_dict, dict):
            print(f"📊 Keys: {list(live_data_dict.keys())}")
            if 'pm2_5' in live_data_dict:
                print(f"📊 PM2.5 count: {len(live_data_dict.get('pm2_5', []))}")
                if len(live_data_dict.get('pm2_5', [])) > 0:
                    print(f"📊 First PM2.5: {live_data_dict['pm2_5'][0]}")
        
        if isinstance(live_data_dict, dict) and 'time' in live_data_dict and len(live_data_dict['time']) > 0:
            try:
                data_df = pd.DataFrame(live_data_dict) 
                
                # Calculate AQI from PM2.5
                predicted_aqi_list = [calculate_aqi_from_pm25(pm) for pm in data_df['pm2_5']]
                
                latest_aqi = round(predicted_aqi_list[-1], 2)
                
                # Get category with alert type (for styling)
                category, alert_type = get_aqi_category_with_class(latest_aqi)
                recommendation = get_health_recommendation(latest_aqi)
                
                # AQI data for card with country information
                aqi_data = {
                    'aqi': latest_aqi,
                    'category': category,
                    'recommendation': recommendation,
                    'country': country,
                    'country_code': country_code,
                    'city_display': city_display
                }
                
                # Pollutants data for display cards
                pollutants_data = {
                    'PM2.5': {
                        'value': round(data_df['pm2_5'].iloc[-1], 2),
                        'unit': 'µg/m³',
                        'icon': '🌫️',
                        'name': 'Particulate Matter 2.5'
                    },
                    'PM10': {
                        'value': round(data_df['pm10'].iloc[-1], 2),
                        'unit': 'µg/m³',
                        'icon': '💨',
                        'name': 'Particulate Matter 10'
                    },
                    'CO': {
                        'value': round(data_df['carbon_monoxide'].iloc[-1], 2),
                        'unit': 'µg/m³',
                        'icon': '☁️',
                        'name': 'Carbon Monoxide'
                    },
                    'NO2': {
                        'value': round(data_df['nitrogen_dioxide'].iloc[-1], 2),
                        'unit': 'µg/m³',
                        'icon': '🏭',
                        'name': 'Nitrogen Dioxide'
                    },
                    'SO2': {
                        'value': round(data_df['sulphur_dioxide'].iloc[-1], 2),
                        'unit': 'µg/m³',
                        'icon': '🌋',
                        'name': 'Sulphur Dioxide'
                    }
                }
                
                # Save to database
                save_to_database(
                    city, latest_aqi, 
                    pollutants_data["PM2.5"]['value'], pollutants_data["PM10"]['value'],
                    pollutants_data["CO"]['value'], pollutants_data["NO2"]['value'], 
                    pollutants_data["SO2"]['value'],
                    category
                )
                
                # Chart data - limit to 48 hours for better visualization
                chart_labels = data_df['time'].tolist()[:48]
                chart_values = [round(aqi, 1) for aqi in predicted_aqi_list[:48]]
                
                chart_data = {
                    'labels': chart_labels,
                    'values': chart_values
                }
                
            except Exception as e:
                print(f"Processing error: {e}")
                aqi_data = None

    return render_template('index_advanced.html', 
                           aqi_data=aqi_data,
                           city=city,
                           pollutants_data=pollutants_data,
                           chart_data=chart_data
                           )

# ============== API ENDPOINTS ==============
@app.route('/api/compare', methods=['POST'])
def compare_cities():
    """Compare AQI of multiple cities"""
    cities = request.json.get('cities', [])
    results = []
    
    for city in cities[:3]:  # Limit to 3 cities
        data, status = fetch_live_aqi_data(city)
        if isinstance(data, dict) and 'pm2_5' in data:
            avg_pm25 = sum(data['pm2_5']) / len(data['pm2_5'])
            aqi = calculate_aqi_from_pm25(avg_pm25)
            category = get_aqi_category_string(aqi)  # Use string version for JSON
            results.append({
                'city': city,
                'aqi': round(aqi, 2),
                'pm25': round(avg_pm25, 2),
                'category': category
            })
    
    return jsonify({'results': results})

@app.route('/api/history/<city>')
def get_city_history(city):
    """Get historical data for a city"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""SELECT city, aqi, pm25, pm10, co, no2, so2, timestamp, category 
                     FROM aqi_records WHERE city=? ORDER BY timestamp DESC LIMIT 50""", (city,))
        rows = c.fetchall()
        conn.close()
        
        history = [{
            'city': r[0], 'aqi': r[1], 'pm25': r[2], 'pm10': r[3], 
            'co': r[4], 'no2': r[5], 'so2': r[6],
            'timestamp': r[7], 'category': r[8]
        } for r in rows]
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all-history')
def get_complete_history():
    """Get all historical data"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if table exists and has data
        c.execute("SELECT COUNT(*) FROM aqi_records")
        count = c.fetchone()[0]
        
        if count == 0:
            conn.close()
            print("⚠️ No records in database yet!")
            return jsonify([])  # Return empty array
        
        c.execute("""SELECT city, aqi, pm25, timestamp, category 
                     FROM aqi_records ORDER BY timestamp DESC LIMIT 100""")
        rows = c.fetchall()
        conn.close()
        
        history = [{
            'city': r[0], 'aqi': r[1], 'pm25': r[2],
            'timestamp': r[3], 'category': r[4]
        } for r in rows]
        
        print(f"✅ Returning {len(history)} history records")
        return jsonify(history)
    except sqlite3.OperationalError as e:
        print(f"❌ Database error: {e}")
        return jsonify([])  # Return empty array if table doesn't exist
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/compare')
def compare_page():
    """City comparison page"""
    return render_template('compare.html')

@app.route('/history')
def history_page():
    """Search history page"""
    return render_template('history.html')

@app.route('/trends')
def trends_page():
    """Weekly trends analysis page"""
    return render_template('index_advanced.html')

@app.route('/rankings')
def rankings_page():
    """City rankings page"""
    return render_template('rankings.html')

@app.route('/api/history')
def get_all_history():
    """Get all search history - NO LIMIT, shows everything"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT city, aqi, pm25, pm10, co, no2, so2, timestamp, category
            FROM aqi_records 
            ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'city': row[0],
                'aqi': round(row[1], 2),
                'pm25': round(row[2], 2) if row[2] else None,
                'pm10': round(row[3], 2) if row[3] else None,
                'co': round(row[4], 2) if row[4] else None,
                'no2': round(row[5], 2) if row[5] else None,
                'so2': round(row[6], 2) if row[6] else None,
                'timestamp': row[7],
                'category': row[8]
            })
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trends/<city>')
def get_trends(city):
    """Get 7-day trends for a city"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DATE(timestamp) as date, AVG(aqi) as avg_aqi, AVG(pm25) as avg_pm25
            FROM aqi_records 
            WHERE city = ? AND timestamp >= datetime('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, (city,))
        rows = cursor.fetchall()
        conn.close()
        
        trends = [{'date': row[0], 'aqi': round(row[1], 2), 'pm25': round(row[2], 2)} for row in rows]
        
        # If no historical data, generate from live API (Demo mode)
        if len(trends) == 0:
            print(f"⚠️ No historical data for {city}, fetching live data...")
            live_data, status = fetch_live_aqi_data(city)
            
            if isinstance(live_data, dict) and 'pm2_5' in live_data and len(live_data['pm2_5']) > 0:
                # Group by day (take every 24th record to simulate daily data)
                from datetime import datetime, timedelta
                today = datetime.now()
                
                demo_trends = []
                for i in range(7):
                    date = (today - timedelta(days=6-i)).strftime('%Y-%m-%d')
                    # Take average of hourly data for that "day" (simulation)
                    start_idx = i * 12 if i * 12 < len(live_data['pm2_5']) else 0
                    end_idx = min(start_idx + 12, len(live_data['pm2_5']))
                    pm25_avg = sum(live_data['pm2_5'][start_idx:end_idx]) / max(len(live_data['pm2_5'][start_idx:end_idx]), 1)
                    aqi = calculate_aqi_from_pm25(pm25_avg)
                    
                    demo_trends.append({
                        'date': date,
                        'aqi': round(aqi, 2),
                        'pm25': round(pm25_avg, 2)
                    })
                
                return jsonify({'city': city, 'trends': demo_trends, 'demo_mode': True})
        
        return jsonify({'city': city, 'trends': trends, 'demo_mode': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rankings')
def get_rankings():
    """Get city rankings by AQI - ONLY from searched cities in history"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First try: Get data from last 24 hours (most relevant)
        cursor.execute("""
            SELECT city, AVG(aqi) as avg_aqi, AVG(pm25) as avg_pm25, COUNT(*) as count, 
                   MAX(category) as category
            FROM aqi_records 
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY city
            HAVING count >= 1
            ORDER BY avg_aqi ASC
        """)
        rows = cursor.fetchall()
        
        # If no data in last 24 hours, get ALL searched cities from history
        if len(rows) == 0:
            cursor.execute("""
                SELECT city, AVG(aqi) as avg_aqi, AVG(pm25) as avg_pm25, COUNT(*) as count,
                       MAX(category) as category
                FROM aqi_records 
                GROUP BY city
                HAVING count >= 1
                ORDER BY avg_aqi ASC
            """)
            rows = cursor.fetchall()
        
        conn.close()
        
        rankings = []
        for idx, row in enumerate(rows, 1):
            rankings.append({
                'rank': idx,
                'city': row[0],
                'aqi': round(row[1], 2),
                'pm25': round(row[2], 2),
                'searches': row[3],
                'category': row[4]
            })
        return jsonify({'rankings': rankings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test-features')
def test_features():
    """Test features page - dark mode, notifications, favorites, sharing, print"""
    return render_template('test_features.html')

@app.route('/api/weather/<city>')
def get_weather(city):
    """Get weather data for a city"""
    try:
        # OpenWeatherMap weather API
        api_key = "fe4feefa8543e06d4f3c66d92c61b69c"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        weather = {
            'temp': round(data['main']['temp'], 1),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': round(data['wind']['speed'], 1),
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon']
        }
        return jsonify(weather)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-api/<city>')
def test_api_connection(city):
    """Test API with exact same method as main search - returns consistent AQI"""
    try:
        # Use exact same data fetcher as main search (returns tuple: data, status_message)
        live_data_dict, status_message = fetch_live_aqi_data(city)
        
        if not isinstance(live_data_dict, dict) or 'pm2_5' not in live_data_dict:
            return jsonify({'error': f'Could not fetch data for {city}'}), 404
        
        # Extract country from status_message (format: "City, Country (Live API Data)")
        country_code = "Unknown"
        country = "Unknown"
        if ", " in status_message:
            parts = status_message.split(", ")
            if len(parts) >= 2:
                country_part = parts[1].split(" (")[0]
                country_code = country_part
                country = get_country_name(country_code)  # Convert to full name
        
        # Calculate AQI exactly like main search does
        latest_pm25 = live_data_dict['pm2_5'][-1] if isinstance(live_data_dict['pm2_5'], list) else live_data_dict['pm2_5']
        latest_aqi = calculate_aqi_from_pm25(latest_pm25)
        
        # Get category with class for styling
        category_text, category_class = get_aqi_category_with_class(latest_aqi)
        
        return jsonify({
            'success': True,
            'city': city,
            'country': country,
            'country_code': country_code,
            'aqi': round(latest_aqi, 2),
            'pm25': round(latest_pm25, 2),
            'category': category_text,
            'source': 'OpenWeatherMap Air Pollution API',
            'note': 'Same data source and calculation as main search'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<format>')
def download_report(format):
    """Download AQI report"""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM aqi_records ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()
        
        if format == 'csv':
            filepath = 'aqi_report.csv'
            df.to_csv(filepath, index=False)
            return send_file(filepath, as_attachment=True, download_name='aqi_report.csv')
        elif format == 'json':
            return jsonify(df.to_dict(orient='records'))
        
        return "Invalid format. Use /download/csv or /download/json", 400
    except Exception as e:
        return f"Error generating report: {str(e)}", 500

# ============== NEW DATA SCIENCE FEATURES ==============

@app.route('/forecast')
def forecast_page():
    """AQI Prediction/Forecasting page"""
    return render_template('forecast.html')

@app.route('/api/forecast/<city>')
def get_forecast(city):
    """Get 7-day AQI forecast using historical data"""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(
            "SELECT timestamp, aqi FROM aqi_records WHERE city=? ORDER BY timestamp",
            conn, params=(city,)
        )
        conn.close()
        
        # If not enough data, fetch live data and create forecast based on it
        if len(df) < 10:
            live_data_tuple = fetch_live_aqi_data(city)
            if not isinstance(live_data_tuple, tuple) or len(live_data_tuple) != 2:
                return jsonify({'error': f'No data available for {city}. Try searching this city first from main dashboard.'}), 400
            
            live_data, status = live_data_tuple
            if not isinstance(live_data, dict) or 'pm2_5' not in live_data or len(live_data['pm2_5']) == 0:
                return jsonify({'error': f'No data available for {city}. Try searching this city first from main dashboard.'}), 400
            
            # Calculate AQI from PM2.5
            current_pm25 = live_data['pm2_5'][-1] if isinstance(live_data['pm2_5'], list) else live_data['pm2_5']
            current_aqi = calculate_aqi_from_pm25(current_pm25)
            forecast_data = []
            historical_data = []
            
            # Generate 7-day forecast with slight variation
            for i in range(1, 8):
                variation = np.random.uniform(-10, 10)
                predicted_aqi = max(0, current_aqi + variation)
                
                forecast_data.append({
                    'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
                    'aqi': round(predicted_aqi, 2),
                    'category': get_aqi_category_string(predicted_aqi),
                    'confidence_low': round(max(0, predicted_aqi - 15), 2),
                    'confidence_high': round(predicted_aqi + 15, 2)
                })
            
            # Add current data as historical
            historical_data.append({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'aqi': round(current_aqi, 2)
            })
            
            return jsonify({
                'city': city,
                'historical': historical_data,
                'forecast': forecast_data,
                'note': 'Forecast based on current AQI. Search city multiple times to build historical data for better predictions.'
            })
        
        # Original code for when we have enough data
        if len(df) < 3:
            return jsonify({'error': 'Need at least 3 records for historical analysis.'}), 400
        
        # Simple moving average forecast
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        df = df.resample('D').mean().fillna(method='ffill')
        
        # Calculate 7-day moving average
        window = min(7, len(df))
        df['forecast'] = df['aqi'].rolling(window=window).mean()
        
        # Generate next 7 days forecast
        last_value = df['forecast'].iloc[-1]
        last_date = df.index[-1]
        
        forecast_data = []
        for i in range(1, 8):
            future_date = last_date + timedelta(days=i)
            # Add slight random variation
            predicted_aqi = last_value + np.random.uniform(-5, 5)
            predicted_aqi = max(0, predicted_aqi)
            
            forecast_data.append({
                'date': future_date.strftime('%Y-%m-%d'),
                'aqi': round(predicted_aqi, 2),
                'category': get_aqi_category_string(predicted_aqi),
                'confidence_low': round(predicted_aqi - 10, 2),
                'confidence_high': round(predicted_aqi + 10, 2)
            })
        
        # Historical data for chart
        historical = df.tail(30).reset_index().to_dict('records')
        historical_data = [{
            'date': record['timestamp'].strftime('%Y-%m-%d'),
            'aqi': round(record['aqi'], 2)
        } for record in historical if not pd.isna(record['aqi'])]
        
        return jsonify({
            'city': city,
            'historical': historical_data,
            'forecast': forecast_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/heatmap')
def heatmap_page():
    """Interactive AQI Heatmap page"""
    return render_template('heatmap.html')

@app.route('/api/heatmap-data')
def get_heatmap_data():
    """Get latest AQI data for multiple cities for heatmap"""
    try:
        # Major cities with coordinates
        cities = [
            {'name': 'Delhi', 'lat': 28.7041, 'lon': 77.1025},
            {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
            {'name': 'Bangalore', 'lat': 12.9716, 'lon': 77.5946},
            {'name': 'Kolkata', 'lat': 22.5726, 'lon': 88.3639},
            {'name': 'Chennai', 'lat': 13.0827, 'lon': 80.2707},
            {'name': 'Hyderabad', 'lat': 17.3850, 'lon': 78.4867},
            {'name': 'Pune', 'lat': 18.5204, 'lon': 73.8567},
            {'name': 'Ahmedabad', 'lat': 23.0225, 'lon': 72.5714},
            {'name': 'Jaipur', 'lat': 26.9124, 'lon': 75.7873},
            {'name': 'Lucknow', 'lat': 26.8467, 'lon': 80.9462},
            {'name': 'Karachi', 'lat': 24.8607, 'lon': 67.0011},
            {'name': 'Lahore', 'lat': 31.5204, 'lon': 74.3587},
            {'name': 'Islamabad', 'lat': 33.6844, 'lon': 73.0479},
        ]
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        map_data = []
        for city_info in cities:
            cursor.execute("""
                SELECT aqi, pm25, category 
                FROM aqi_records 
                WHERE city=? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (city_info['name'],))
            
            result = cursor.fetchone()
            if result:
                aqi, pm25, category = result
            else:
                # Fetch live data if not in database
                live_data_tuple = fetch_live_aqi_data(city_info['name'])
                if isinstance(live_data_tuple, tuple):
                    live_data, status = live_data_tuple
                else:
                    live_data = live_data_tuple
                    
                if live_data and isinstance(live_data, dict):
                    aqi = live_data.get('aqi', 50)
                    pm25 = live_data.get('pm25', 25)
                    category = get_aqi_category_string(aqi)
                else:
                    # Default values if fetch fails
                    aqi = 50
                    pm25 = 25
                    category = "Moderate 😐"
            
            map_data.append({
                'city': city_info['name'],
                'lat': city_info['lat'],
                'lon': city_info['lon'],
                'aqi': round(aqi, 2),
                'pm25': round(pm25, 2) if pm25 else 0,
                'category': category
            })
        
        conn.close()
        return jsonify({'cities': map_data})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics')
def analytics_page():
    """Advanced Analytics Dashboard"""
    return render_template('analytics.html')

@app.route('/api/analytics/<city>')
def get_analytics(city):
    """Get statistical analysis for a city"""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(
            "SELECT * FROM aqi_records WHERE city=? ORDER BY timestamp",
            conn, params=(city,)
        )
        conn.close()
        
        # If not enough data in database, fetch live data and show current stats
        if len(df) < 5:
            live_data_tuple = fetch_live_aqi_data(city)
            if isinstance(live_data_tuple, tuple) and len(live_data_tuple) == 2:
                live_data, status = live_data_tuple
                if isinstance(live_data, dict) and 'pm2_5' in live_data and len(live_data['pm2_5']) > 0:
                    # Calculate current AQI from live data
                    pm25_values = live_data['pm2_5']
                    aqi_values = [calculate_aqi_from_pm25(pm) for pm in pm25_values]
                    
                    # Create analytics from current data
                    analytics = {
                        'city': city,
                        'total_records': len(aqi_values),
                        'note': 'Data from current live feed. Search this city multiple times to build historical data for better analysis.',
                        'statistics': {
                            'aqi_mean': round(sum(aqi_values) / len(aqi_values), 2),
                            'aqi_median': round(sorted(aqi_values)[len(aqi_values)//2], 2),
                            'aqi_std': round(pd.Series(aqi_values).std(), 2),
                            'aqi_min': round(min(aqi_values), 2),
                            'aqi_max': round(max(aqi_values), 2),
                            'pm25_mean': round(sum(pm25_values) / len(pm25_values), 2),
                            'pm10_mean': round(sum(live_data.get('pm10', pm25_values)) / len(pm25_values), 2) if 'pm10' in live_data else 0,
                        },
                        'category_distribution': {},
                        'trend': 'stable'
                    }
                    
                    # Calculate category distribution
                    from collections import Counter
                    categories = [get_aqi_category_string(aqi) for aqi in aqi_values]
                    analytics['category_distribution'] = dict(Counter(categories))
                    
                    return jsonify(analytics)
            
            return jsonify({'error': f'Not enough data for analysis. Please search "{city}" from the main dashboard first to collect data.'}), 400
        
        # Basic statistics
        analytics = {
            'city': city,
            'total_records': len(df),
            'statistics': {
                'aqi_mean': round(df['aqi'].mean(), 2),
                'aqi_median': round(df['aqi'].median(), 2),
                'aqi_std': round(df['aqi'].std(), 2),
                'aqi_min': round(df['aqi'].min(), 2),
                'aqi_max': round(df['aqi'].max(), 2),
                'pm25_mean': round(df['pm25'].mean(), 2) if 'pm25' in df else 0,
                'pm10_mean': round(df['pm10'].mean(), 2) if 'pm10' in df else 0,
            },
            'category_distribution': df['category'].value_counts().to_dict(),
            'trend': 'improving' if df['aqi'].iloc[-5:].mean() < df['aqi'].iloc[:5].mean() else 'worsening'
        }
        
        # Correlation analysis
        numeric_cols = ['aqi', 'pm25', 'pm10', 'co', 'no2', 'so2']
        available_cols = [col for col in numeric_cols if col in df.columns]
        if len(available_cols) > 1:
            corr_matrix = df[available_cols].corr()
            analytics['correlations'] = corr_matrix.to_dict()
        
        return jsonify(analytics)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calculator')
def calculator_page():
    """AQI Calculator page"""
    return render_template('calculator.html')

@app.route('/api/calculate-aqi', methods=['POST'])
def calculate_aqi():
    """Calculate AQI from pollutant concentrations"""
    try:
        data = request.json
        
        # Get pollutant values
        pm25 = float(data.get('pm25', 0))
        pm10 = float(data.get('pm10', 0))
        co = float(data.get('co', 0))
        no2 = float(data.get('no2', 0))
        so2 = float(data.get('so2', 0))
        o3 = float(data.get('o3', 0))
        
        # Calculate individual AQI for each pollutant
        def calc_pollutant_aqi(concentration, breakpoints):
            for bp in breakpoints:
                if bp['c_low'] <= concentration <= bp['c_high']:
                    aqi = ((bp['i_high'] - bp['i_low']) / (bp['c_high'] - bp['c_low'])) * \
                          (concentration - bp['c_low']) + bp['i_low']
                    return round(aqi, 2)
            return 500  # Hazardous
        
        # PM2.5 breakpoints (µg/m³)
        pm25_bp = [
            {'c_low': 0, 'c_high': 12, 'i_low': 0, 'i_high': 50},
            {'c_low': 12.1, 'c_high': 35.4, 'i_low': 51, 'i_high': 100},
            {'c_low': 35.5, 'c_high': 55.4, 'i_low': 101, 'i_high': 150},
            {'c_low': 55.5, 'c_high': 150.4, 'i_low': 151, 'i_high': 200},
            {'c_low': 150.5, 'c_high': 250.4, 'i_low': 201, 'i_high': 300},
            {'c_low': 250.5, 'c_high': 500, 'i_low': 301, 'i_high': 500},
        ]
        
        # Calculate AQI for PM2.5
        aqi_pm25 = calc_pollutant_aqi(pm25, pm25_bp) if pm25 > 0 else 0
        
        # Simplified: use PM2.5 as primary pollutant for now
        final_aqi = aqi_pm25
        category = get_aqi_category(final_aqi)
        
        result = {
            'aqi': round(final_aqi, 2),
            'category': category,
            'primary_pollutant': 'PM2.5',
            'pollutant_aqis': {
                'pm25': aqi_pm25,
            },
            'health_message': get_health_message(category)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/compare-advanced')
def compare_advanced_page():
    """Enhanced multi-city comparison with statistics"""
    return render_template('compare_advanced.html')

@app.route('/api/compare-stats', methods=['POST'])
def compare_statistics():
    """Compare multiple cities with statistical tests - includes country names"""
    try:
        data = request.json
        cities = data.get('cities', [])
        
        if len(cities) < 2:
            return jsonify({'error': 'Need at least 2 cities to compare'}), 400
        
        conn = get_db_connection()
        
        comparison_data = []
        city_aqi_values = {}
        
        for city in cities:
            # Get country code for this city
            country_code = "Unknown"
            try:
                # Fetch live data to get country code
                live_data_tuple = fetch_live_aqi_data(city)
                if isinstance(live_data_tuple, tuple) and len(live_data_tuple) == 2:
                    live_data, status = live_data_tuple
                    # Extract country from status string (format: "City, CC")
                    if isinstance(status, str) and ',' in status:
                        parts = status.split(',')
                        if len(parts) >= 2:
                            country_code = parts[-1].strip().split()[0]  # Get country code
            except:
                pass
            
            # First try to get from database
            df = pd.read_sql_query(
                "SELECT aqi, pm25, pm10, timestamp FROM aqi_records WHERE city=? ORDER BY timestamp DESC LIMIT 50",
                conn, params=(city,)
            )
            
            # If no data in database, fetch live data
            if len(df) == 0:
                live_data_tuple = fetch_live_aqi_data(city)
                if isinstance(live_data_tuple, tuple) and len(live_data_tuple) == 2:
                    live_data, status = live_data_tuple
                    if isinstance(live_data, dict) and 'pm2_5' in live_data and len(live_data['pm2_5']) > 0:
                        # Calculate AQI from PM2.5
                        avg_pm25 = sum(live_data['pm2_5']) / len(live_data['pm2_5'])
                        avg_pm10 = sum(live_data['pm10']) / len(live_data['pm10']) if 'pm10' in live_data else avg_pm25 * 1.5
                        aqi = calculate_aqi_from_pm25(avg_pm25)
                        df = pd.DataFrame([{
                            'aqi': aqi,
                            'pm25': avg_pm25,
                            'pm10': avg_pm10,
                            'timestamp': datetime.now().isoformat()
                        }])
            
            if len(df) > 0:
                aqi_values = df['aqi'].tolist()
                city_aqi_values[city] = aqi_values
                
                # Handle ALL edge cases: NaN, Infinity, -Infinity
                mean_val = df['aqi'].mean()
                median_val = df['aqi'].median()
                std_val = df['aqi'].std()
                min_val = df['aqi'].min()
                max_val = df['aqi'].max()
                current_val = df['aqi'].iloc[0]
                
                # Replace NaN/Infinity with safe defaults
                if pd.isna(mean_val) or mean_val == float('inf') or mean_val == float('-inf'): 
                    mean_val = 0.0
                if pd.isna(median_val) or median_val == float('inf') or median_val == float('-inf'): 
                    median_val = 0.0
                if pd.isna(std_val) or std_val == float('inf') or std_val == float('-inf'): 
                    std_val = 0.0
                if pd.isna(min_val) or min_val == float('inf') or min_val == float('-inf'): 
                    min_val = 0.0
                if pd.isna(max_val) or max_val == float('inf') or max_val == float('-inf'): 
                    max_val = 0.0
                if pd.isna(current_val) or current_val == float('inf') or current_val == float('-inf'): 
                    current_val = 0.0
                
                comparison_data.append({
                    'city': city,
                    'country': country_code,
                    'city_with_country': f"{city}, {country_code}",
                    'current_aqi': round(float(current_val), 2),
                    'mean_aqi': round(float(mean_val), 2),
                    'median_aqi': round(float(median_val), 2),
                    'std_aqi': round(float(std_val), 2),
                    'min_aqi': round(float(min_val), 2),
                    'max_aqi': round(float(max_val), 2),
                    'data_points': int(len(df))
                })
        
        conn.close()
        
        # Statistical tests
        statistical_tests = {}
        if len(city_aqi_values) >= 2:
            city_names = list(city_aqi_values.keys())
            
            # T-test for first two cities
            if len(city_aqi_values[city_names[0]]) > 1 and len(city_aqi_values[city_names[1]]) > 1:
                t_stat, p_value = stats.ttest_ind(
                    city_aqi_values[city_names[0]],
                    city_aqi_values[city_names[1]]
                )
                # Handle NaN values
                if pd.isna(t_stat): t_stat = 0.0
                if pd.isna(p_value): p_value = 1.0
                
                is_significant = bool(p_value < 0.05)  # Convert to Python bool
                statistical_tests['t_test'] = {
                    'cities': [city_names[0], city_names[1]],
                    't_statistic': round(float(t_stat), 4),
                    'p_value': round(float(p_value), 4),
                    'significant': is_significant,
                    'interpretation': f"{'Significantly different' if is_significant else 'Not significantly different'} (α=0.05)"
                }
            
            # ANOVA for all cities
            if len(city_aqi_values) > 2:
                try:
                    f_stat, p_value = stats.f_oneway(*city_aqi_values.values())
                    # Handle NaN values
                    if pd.isna(f_stat): f_stat = 0.0
                    if pd.isna(p_value): p_value = 1.0
                    
                    is_significant = bool(p_value < 0.05)  # Convert to Python bool
                    statistical_tests['anova'] = {
                        'f_statistic': round(float(f_stat), 4),
                        'p_value': round(float(p_value), 4),
                        'significant': is_significant,
                        'interpretation': f"{'At least one city is significantly different' if is_significant else 'No significant difference among cities'} (α=0.05)"
                    }
                except:
                    pass
        
        # Correlation matrix
        correlation_matrix = {}
        if len(comparison_data) > 1:
            means = [city['mean_aqi'] for city in comparison_data]
            city_names_list = [city['city'] for city in comparison_data]
            
            for i, city1 in enumerate(city_names_list):
                correlation_matrix[city1] = {}
                for j, city2 in enumerate(city_names_list):
                    if city1 in city_aqi_values and city2 in city_aqi_values:
                        min_len = min(len(city_aqi_values[city1]), len(city_aqi_values[city2]))
                        if min_len > 1:
                            corr, _ = stats.pearsonr(
                                city_aqi_values[city1][:min_len],
                                city_aqi_values[city2][:min_len]
                            )
                            # Handle NaN correlation values
                            if pd.isna(corr):
                                correlation_matrix[city1][city2] = 0.0
                            else:
                                correlation_matrix[city1][city2] = round(float(corr), 3)
                        else:
                            correlation_matrix[city1][city2] = 0.0
                    else:
                        correlation_matrix[city1][city2] = 0.0
        
        result = {
            'comparison': comparison_data,
            'statistical_tests': statistical_tests,
            'correlation_matrix': correlation_matrix,
            'best_city': min(comparison_data, key=lambda x: x['mean_aqi'])['city'],
            'worst_city': max(comparison_data, key=lambda x: x['mean_aqi'])['city']
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_health_message(category):
    """Get health message based on AQI category"""
    messages = {
        'Good': 'Air quality is satisfactory, and air pollution poses little or no risk.',
        'Moderate': 'Air quality is acceptable. However, there may be a risk for some people.',
        'Unhealthy for Sensitive Groups': 'Members of sensitive groups may experience health effects.',
        'Unhealthy': 'Some members of the general public may experience health effects.',
        'Very Unhealthy': 'Health alert: The risk of health effects is increased for everyone.',
        'Hazardous': 'Health warning of emergency conditions: everyone is more likely to be affected.'
    }
    return messages.get(category, 'Unknown air quality level.')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
