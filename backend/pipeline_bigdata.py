# pipiline_bigdata.py

import os, math, warnings
import numpy as np
import pandas as pd
import dask.dataframe as dd
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
from dask_ml.model_selection import train_test_split as dask_train_test_split
from distributed import Client 
import xgboost.dask as xgb_dask
import joblib

warnings.filterwarnings("ignore")
os.makedirs("models", exist_ok=True)
pd.set_option('display.max_columns', None)


# 🛑 WINDOWS FIX: POORE EXECUTION CODE KO IS BLOCK MEIN DALNA ZAROORI HAI
if __name__ == '__main__':
    
    # --------------------------------------------------------------
    # 1️⃣  Simulate Big Dataset (1 Million Rows) aur Parquet Saving
    # --------------------------------------------------------------
    print("Generating 1 Million row Big Data (Synthetic) ...")
    np.random.seed(42)
    # Safe date range
    dates = pd.date_range(start="1950-01-01", end="2250-12-31", freq="D") 
    n = len(dates)

    data = pd.DataFrame({
        "date": dates,
        "PM2_5": np.abs(np.random.normal(60, 25, n)),
        "PM10": np.abs(np.random.normal(90, 30, n)),
        "NO2": np.abs(np.random.normal(35, 10, n)),
        "CO": np.abs(np.random.normal(0.9, 0.3, n)),
        "SO2": np.abs(np.random.normal(15, 5, n)),
        "Temperature": np.random.normal(28, 5, n),
        "Humidity": np.random.normal(55, 10, n)
    })

    data["AQI"] = (0.5 * data["PM2_5"] + 0.3 * data["PM10"] + 0.1 * data["NO2"] + 0.05 * data["SO2"] + np.random.normal(0, 10, n))

    def aqi_category(aqi):
        if aqi <= 50: return "Good"
        elif aqi <= 100: return "Moderate"
        elif aqi <= 150: return "Unhealthy_Sensitive"
        elif aqi <= 200: return "Unhealthy"
        elif aqi <= 300: return "Very_Unhealthy"
        else: return "Hazardous"

    data["AQI_Category"] = data["AQI"].apply(aqi_category)
    print(f"Dataset ready with shape: {data.shape} (Approx {n} Rows)")

    data.to_parquet("aqi_millions.parquet", index=False)
    del data
    print("Pandas DataFrame memory se hata diya. Data Parquet mein save hai.")

    # --------------------------------------------------------------
    # 2️⃣  Dask Data Loading aur Feature Engineering (Scalable)
    # --------------------------------------------------------------
    print("\nLoading data with Dask and adding Lagged Features...")

    data_dd = dd.read_parquet("aqi_millions.parquet")
    print(f"Dask DataFrame loaded with {data_dd.npartitions} partitions (cores).")

    data_dd["date"] = dd.to_datetime(data_dd["date"])
    data_dd = data_dd.set_index("date", sorted=True)

    data_dd['PM2_5_lag1'] = data_dd['PM2_5'].shift(1)
    data_dd['AQI_lag1'] = data_dd['AQI'].shift(1)
    data_dd['PM2_5_roll7d'] = data_dd['PM2_5'].rolling(window='7D').mean().shift(1)

    data_dd = data_dd.dropna()
    data_dd["month"] = data_dd.index.month
    data_dd["dayofweek"] = data_dd.index.dayofweek

    # --------------------------------------------------------------
    # 3️⃣  Modeling Data Split (Dask-ML)
    # --------------------------------------------------------------
    print("Splitting data for Dask-ML...")
    features = [
        "PM2_5","PM10","NO2","CO","SO2","Temperature","Humidity",
        "month","dayofweek",
        "PM2_5_lag1", "AQI_lag1", "PM2_5_roll7d"
    ]
    X = data_dd[features]
    y_reg = data_dd["AQI"]
    y_clf = data_dd["AQI_Category"]

    le = LabelEncoder()
    y_clf_computed = y_clf.compute()
    y_clf_enc = le.fit_transform(y_clf_computed)
    joblib.dump(le, "models/label_encoder.pkl")

    X_train, X_test, y_reg_train, y_reg_test = dask_train_test_split(
        X, y_reg, test_size=0.2, random_state=42)

    # --------------------------------------------------------------
    # 4️⃣  XGBoost Regression Modeling (Highly Scalable)
    # --------------------------------------------------------------

    print("\nStarting Dask Local Client...")
    client = None
    try:
        # client ko shuru kiya gaya
        client = Client(n_workers=4, threads_per_worker=1, processes=True)
        print(f"Dask Client started successfully! Dashboard Link: {client.dashboard_link}")
    except Exception as e:
        print(f"Could not start Dask Client: {e}. Check distributed package installation.")

    print("Training XGBoost Regression model (Dask-XGBoost) ... This may take a few minutes.")

    reg = xgb_dask.DaskXGBRegressor(
        n_estimators=150, 
        tree_method='hist', 
        random_state=42, 
        n_jobs=-1 
    )

    reg.fit(X_train, y_reg_train)

    # --------------------------------------------------------------
    # 5️⃣  Model Evaluation (Dask-ML)
    # --------------------------------------------------------------
    print("\nRegression Evaluation:")
    y_pred_reg = reg.predict(X_test).compute()
    y_reg_test_computed = y_reg_test.compute()

    print("  RMSE:", math.sqrt(mean_squared_error(y_reg_test_computed, y_pred_reg)))
    print("  R²  :", r2_score(y_reg_test_computed, y_pred_reg))

    # --------------------------------------------------------------
    # 6️⃣  Save Model aur Client Band Karna
    # --------------------------------------------------------------
    joblib.dump(reg, "models/aqi_regression_model.pkl")
    print("\n✅ Pipeline completed successfully. Model saved to models/aqi_regression_model.pkl")

    # Client ko band karna
    if client:
        client.close()
        print("Dask Client closed.")