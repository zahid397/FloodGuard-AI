import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

def train_model():
    """
    Train a simple flood prediction model and save it as flood_model.pkl
    """

    DATA_PATH = "flood_data.csv"  # Root-level CSV
    MODEL_PATH = "model/flood_model.pkl"

    if not os.path.exists(DATA_PATH):
        print("❌ Dataset not found. Please make sure 'flood_data.csv' exists.")
        return

    # Load dataset
    data = pd.read_csv(DATA_PATH)

    # Basic preprocessing
    features = ["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"]
    target = "flood_risk"

    if not all(col in data.columns for col in features + [target]):
        print("⚠️ Dataset missing required columns!")
        print(f"Required columns: {features + [target]}")
        return

    X = data[features]
    y = data[target].map({"low": 0, "medium": 1, "high": 2})

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Save the trained model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"✅ Model trained and saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
