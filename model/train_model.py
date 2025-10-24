# train_model.py
# FloodGuard AI Model Training Script
# Author: Zahid Hasan

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

def train_model(data_path="data/flood_data.csv", model_dir="model"):
    """
    Trains the flood prediction model and saves it as model/flood_model.pkl
    """
    try:
        # === 📂 Load dataset ===
        df = pd.read_csv(data_path)
        print(f"✅ Data loaded successfully: {df.shape[0]} rows")

        # === 🧩 Feature and Target columns ===
        feature_cols = ["MonsoonIntensity", "Topography", "Drainage", "SoilType", "Urbanization"]
        target_col = "FloodRisk"

        if not all(col in df.columns for col in feature_cols + [target_col]):
            raise ValueError("❌ Dataset missing one or more required columns.")

        X = df[feature_cols]
        y = df[target_col]

        # === ✂️ Train-test split ===
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # === 🧠 Train RandomForest model ===
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)

        # === 📊 Evaluate model ===
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"📈 Model Accuracy: {acc:.2%}")

        # === 💾 Save model ===
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "flood_model.pkl")
        joblib.dump(model, model_path)

        print(f"✅ Model saved successfully at {model_path}")
        return model_path

    except FileNotFoundError:
        print("❌ Error: Dataset not found. Please check 'data/flood_data.csv'.")
    except Exception as e:
        print(f"⚠️ Unexpected Error: {e}")

# === 🔧 Run directly ===
if __name__ == "__main__":
    train_model()
