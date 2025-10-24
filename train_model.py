# train.py
# FloodGuard-AI: Flood Risk Prediction Model Trainer
# Author: Zahid Hasan

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train_flood_model(data_path="data/flood_data.csv", model_dir="model"):
    """
    Trains a Random Forest model on flood risk data and saves it locally.
    """
    try:
        # ডেটা লোড
        df = pd.read_csv(data_path)
        print(f"✅ Data loaded successfully: {len(df)} rows")

        # ইনপুট ও আউটপুট কলাম নির্ধারণ
        feature_cols = ["MonsoonIntensity", "Topography", "Drainage", "SoilType", "Urbanization"]
        target_col = "FloodRisk"

        X = df[feature_cols]
        y = df[target_col]

        # ট্রেন/টেস্ট ভাগ
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # মডেল তৈরি ও ট্রেইন
        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=None,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)

        # একুরেসি রিপোর্ট
        acc = model.score(X_test, y_test)
        print(f"📊 Model Accuracy: {acc:.2%}")

        # মডেল সংরক্ষণ
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "flood_model.pkl")
        joblib.dump(model, model_path)

        print(f"✅ Model trained successfully and saved to {model_path}")

    except FileNotFoundError:
        print("❌ Error: flood_data.csv file not found. Please check the data path.")
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")

if __name__ == "__main__":
    train_flood_model()
