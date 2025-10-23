import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib, os

print("🔹 Loading dataset...")
data = pd.read_csv("flood_data.csv")

# Clean non-numeric values
data = data.apply(pd.to_numeric, errors='coerce')
data = data.dropna()

# Split features and target
X = data[["rainfall", "humidity", "temperature", "river_level", "pressure"]]
y = data["flood_risk"]

print("🔹 Training model...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/flood_model.pkl")

print("✅ Model trained successfully and saved to model/flood_model.pkl")
