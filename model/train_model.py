# model/train_model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
import os

def train_model():

    # === Load CSV Dataset ===
    df = pd.read_csv("data/flood_training_data.csv")

    print("📂 Dataset Loaded:", df.shape)

    # === Features & Labels ===
    X = df[["rainfall_mm", "temperature_c", "humidity_percent", "water_level_m"]]
    y = df["flood_risk"]

    # === Train-Test Split ===
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # === ML Model (Improved Version) ===
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=7,
        min_samples_split=2,
        random_state=42
    )

    model.fit(X_train, y_train)

    # === Evaluate Model ===
    y_pred = model.predict(X_test)
    print("\n📊 Model Performance Report:\n")
    print(classification_report(y_test, y_pred))

    # === Save Model to Folder ===
    os.makedirs("model", exist_ok=True)
    with open("model/flood_model.pkl", "wb") as f:
        pickle.dump(model, f)

    print("\n✅ FloodGuard AI Model trained and saved successfully!")

if __name__ == "__main__":
    train_model()
