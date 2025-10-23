import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# ===============================
# 📂 Load Dataset
# ===============================
df = pd.read_csv("data/flood_data.csv")

# Feature columns
X = df[["rainfall", "humidity", "temperature", "river_level", "pressure"]]
y = df["flood_risk"]

# ===============================
# 🔀 Train-Test Split
# ===============================
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ===============================
# 🤖 Train Model
# ===============================
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ===============================
# 💾 Save Model
# ===============================
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/flood_model.pkl")

print("✅ Model trained and saved as model/flood_model.pkl")
