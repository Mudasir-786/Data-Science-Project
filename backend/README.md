# Backend folder structure documentation

This folder contains all backend Python code for the AQI Monitoring System.

## Structure

```
backend/
├── app.py                      # Main Flask application (1100 lines)
├── data_fetcher.py             # OpenWeatherMap API integration
├── pipeline_bigdata.py         # ML training pipeline
├── db_helper.py                # Database connection helper
├── requirements.txt            # Python dependencies
│
├── models/                     # Trained ML models
│   ├── aqi_regression_model.pkl    # XGBoost model (R²=0.682)
│   └── label_encoder.pkl           # Category encoder
│
└── data/                       # Training datasets
    └── aqi_millions.parquet        # 109,938 rows synthetic data
```

## Main Components

### 1. app.py
Main Flask application with 20+ routes:
- `/` - Main dashboard
- `/compare` - 3-city comparison
- `/compare-advanced` - 5-city statistical comparison
- `/forecast` - 7-day predictions
- `/analytics` - Statistical analysis
- `/heatmap` - Geographic visualization
- `/history` - Search history
- `/rankings` - City rankings
- `/calculator` - AQI calculator

### 2. data_fetcher.py
Handles all API communication:
- Fetches real-time AQI data from OpenWeatherMap
- Reverse geocoding with Nominatim
- Fallback to dummy data if API fails
- Returns tuple: (data_dict, status_message)

### 3. pipeline_bigdata.py
Machine Learning training pipeline:
- Generates synthetic dataset (109,938 rows)
- Uses Dask for distributed computing
- Trains XGBoost regression model
- Saves trained model as pickle file

### 4. db_helper.py
Database utility functions:
- Connection management
- Path resolution for SQLite database
- Used across all routes

## API Endpoints

### Core Endpoints
- `POST /api/compare` - Compare multiple cities
- `GET /api/history/<city>` - Get city history
- `GET /api/forecast/<city>` - Get 7-day forecast
- `POST /api/compare-stats` - Statistical comparison
- `GET /api/rankings` - City rankings
- `GET /api/analytics/<city>` - Statistical analysis
- `POST /api/calculate-aqi` - Manual AQI calculation

## Database

SQLite database (`aqi_history.db`) stored in project root:
- Table: `aqi_records`
- Fields: city, aqi, pm25, pm10, co, no2, so2, timestamp, category
- Unlimited storage

## Machine Learning Model

**Algorithm**: XGBoost Gradient Boosting
- Type: Regression
- Performance: R²=0.682, RMSE=10.28
- Trees: 150
- Features: 12 (pollutants + lag features)
- Training samples: 109,938

## Running the Backend

```bash
cd backend
python app.py
```

Server starts at: http://127.0.0.1:5000
