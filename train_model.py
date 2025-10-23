import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle
import os

def train_model():
    # ডেটাসেট লোড করো
    df = pd.read_csv("data/flood_data.csv")

    # Feature (X) এবং Target (y) আলাদা করো
    X = df[['rainfall', 'temperature', 'humidity', 'river_level']]
    y = df['flood_occurred']  # বা তোমার target কলামের নাম

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # মডেল তৈরি ও ট্রেন
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # মডেল সংরক্ষণ করো
    os.makedirs("model", exist_ok=True)
    with open("model/flood_model.pkl", "wb") as file:
        pickle.dump(model, file)

    print("✅ Model trained and saved successfully!")
