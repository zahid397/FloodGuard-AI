import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib, os

df = pd.read_csv("flood_data.csv")  # ফাইলের নাম একদম ঠিক থাকতে হবে!

X = df[["MonsoonIntensity", "Topography", "Drainage", "SoilType", "Urbanization"]]
y = df["FloodRisk"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/flood_model.pkl")

print("✅ Model trained successfully!")
