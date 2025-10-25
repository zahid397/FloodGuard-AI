# model/train_model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

def train_model():
    # Dummy flood dataset
    data = {
        "rainfall_mm": [50, 120, 250, 400, 80, 20, 10, 300, 280, 150],
        "temperature_c": [28, 30, 26, 25, 29, 35, 33, 24, 27, 31],
        "humidity_percent": [80, 85, 90, 95, 70, 65, 60, 92, 88, 75],
        "water_level_m": [4.5, 5.0, 7.2, 8.0, 3.5, 2.0, 1.5, 9.0, 6.5, 4.0],
        "flood_risk": [0, 1, 2, 2, 0, 0, 0, 2, 1, 1],
    }

    df = pd.DataFrame(data)

    X = df[["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"]]
    y = df["flood_risk"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    os.makedirs("model", exist_ok=True)
    with open("model/flood_model.pkl", "wb") as f:
        pickle.dump(model, f)

    print("✅ FloodGuard AI Model trained successfully!")
