# AQI Monitoring & Prediction System
**Advanced Air Quality Index Dashboard with Machine Learning**  
Python | Flask | XGBoost | Dask | SQLite | Chart.js | Plotly

**Academic Project | Data Science Course | 5th Semester**  
University: Sukkur IBA University, Khairpur Campus  
Submitted to: [Professor/Instructor Name]  
Date: December 2025  

---

## 📋 Table of Contents
- Overview
- Features
- Project Structure
- Technology Stack
- Installation
- Usage
- API Endpoints
- Machine Learning Model
- Dataset Information
- Contributing
- License
- Contact

---

## 🎯 Overview
The AQI Monitoring & Prediction System is a comprehensive web-based application designed to monitor, analyze, and predict Air Quality Index (AQI) across multiple cities worldwide. Built with Flask and powered by XGBoost machine learning algorithms, this system provides real-time air quality data, historical trends, statistical analysis, and 7-day forecasts.

**Key Highlights**
- Real-time AQI monitoring from OpenWeatherMap API
- Machine Learning predictions using XGBoost (R² = 0.682, RMSE = 10.28)
- Big Data processing with Dask (109,938 training samples)
- Statistical analysis (T-test, ANOVA, Pearson correlation)
- Interactive visualizations with Chart.js and Plotly
- Multi-city comparison with country name display
- 7-day AQI forecasting with confidence intervals
- Unlimited search history stored in SQLite database

---

## ✨ Features
**Real-Time AQI Dashboard**
- Live air quality data for any city worldwide
- EPA standard AQI calculation from PM2.5
- Health recommendations based on AQI levels
- Country name display for global context

**Multi-City Comparison**
- Compare 3-5 cities simultaneously
- Statistical significance testing (T-test, ANOVA)
- Correlation matrix visualization
- Best/worst city identification

**Historical Trends Analysis**
- Unlimited search history storage
- 7-day, 30-day trend visualization
- City rankings based on average AQI
- Category distribution analysis

**AQI Forecasting**
- 7-day ahead predictions using historical data
- Confidence intervals for predictions
- Moving average smoothing
- Time series visualization

**Advanced Analytics**
- Statistical summaries (mean, median, std, min, max)
- Pollutant correlation analysis
- Category distribution charts
- Trend direction indicators (improving/worsening)

**Interactive Heatmap**
- Geographic AQI visualization
- Major cities coverage (India, Pakistan)
- Color-coded intensity markers
- Real-time data integration

**AQI Calculator**
- Manual AQI calculation from pollutant values
- EPA breakpoint formula implementation
- Primary pollutant identification
- Health message generation

---

## 📁 Project Structure
DS-Project-1/
├── backend/
│ ├── app.py
│ ├── data_fetcher.py
│ ├── pipeline_bigdata.py
│ ├── models/
│ │ ├── aqi_regression_model.pkl
│ │ └── label_encoder.pkl
│ └── data/
│ └── aqi_millions.parquet
├── frontend/
│ ├── templates/
│ └── static/
├── aqi_history.db
├── requirements.txt
├── .gitignore
├── README.md
└── LICENSE


---

## 🛠️ Technology Stack
**Backend:** Python, Flask, XGBoost, Dask, Pandas, NumPy, Scikit-learn, SciPy, SQLite, Requests  
**Frontend:** HTML5, Bootstrap 5, Chart.js, Plotly, JavaScript ES6, Folium  
**APIs:** OpenWeatherMap Air Pollution API, Nominatim OSM

---

## 📦 Installation
**Prerequisites:** Python 3.13+, pip, Git, OpenWeatherMap API key  
1. Clone repository:  
git clone https://github.com/Mudasir786/AQI-Monitoring-Prediction.git
cd AQI-Monitoring-Prediction

2. Install dependencies:  
pip install -r requirements.txt

3. Initialize database:  
cd backend
python app.py

4. Train ML model (optional, pre-trained included):  
python pipeline_bigdata.py


---

## 🚀 Usage
Start the application:  
cd backend
python app.py

Access the dashboard: `http://127.0.0.1:5000`

**Endpoints:**  
- `/` – Main Dashboard  
- `/compare` – 3-City Comparison  
- `/compare-advanced` – 5-City Statistics  
- `/forecast` – 7-Day Forecast  
- `/analytics` – Analytics  
- `/heatmap` – Heatmap  
- `/history` – Search History  
- `/rankings` – City Rankings  
- `/calculator` – AQI Calculator

---

## 🤖 Machine Learning Model
**Algorithm:** XGBoost Gradient Boosting (Regression)  
**R² Score:** 0.682 | **RMSE:** 10.28 AQI points  
**Training Samples:** 109,938 | **Features:** 12  


---

## 📧 Contact
- GitHub: [Mudasir786](https://github.com/Mudasir786)  
- Email: mudasirhussainlaghari49@gmail.com

---

**Acknowledgments:**  
- OpenWeatherMap, EPA, XGBoost, Dask, Flask, Bootstrap, Chart.js
