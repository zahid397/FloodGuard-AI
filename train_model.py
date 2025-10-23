import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib, os

print("🔹 Loading dataset...")
data = pd.read_csv("flood_data.csv")

# Clean up — remove invalid and non-numeric values
for col in ["rainfall", "humidity", "temperature", "river_level", "pressure", "flood_risk"]:
    data[col] = pd.to_numeric(data[col], errors="coerce")

# Drop rows with missing or invalid data
data = data.dropna(subset=["rainfall", "humidity", "temperature", "river_level", "pressure", "flood_risk"])

# Ensure correct data types
data = data.astype({
    "rainfall": "float64",
    "humidity": "float64",
    "temperature": "float64",
    "river_level": "float64",
    "pressure": "float64",
    "flood_risk": "int64"
})

print(f"✅ Cleaned data: {data.shape[0]} valid rows remain")

# Split features and labels
X = data[["rainfall", "humidity", "temperature", "river_level", "pressure"]]
y = data["flood_risk"]

print("🔹 Training model...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/flood_model.pkl")

print("✅ Model trained successfully and saved to model/flood_model.pkl")
