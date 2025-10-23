import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib, os

print("🔹 Loading dataset...")

# CSV load
data = pd.read_csv("flood_data.csv")

# Clean all text and non-numeric issues
for col in ["rainfall", "humidity", "temperature", "river_level", "pressure", "flood_risk"]:
    data[col] = pd.to_numeric(data[col], errors="coerce")

# Drop missing rows
data = data.dropna()

# Feature selection
X = data[["rainfall", "humidity", "temperature", "river_level", "pressure"]]
y = data["flood_risk"].astype(int)  # ensure integer labels

print("✅ Data cleaned successfully!")

# Split and train model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("🔹 Training model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/flood_model.pkl")

print("✅ Model trained successfully and saved to model/flood_model.pkl")
