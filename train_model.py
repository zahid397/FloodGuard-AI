import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib, os

# ডেটা লোড
df = pd.read_csv("data/flood_data.csv")

# ইনপুট ও আউটপুট কলাম
X = df[["MonsoonIntensity", "Topography", "Drainage", "SoilType", "Urbanization"]]
y = df["FloodRisk"]

# ট্রেন/টেস্ট স্প্লিট
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# মডেল ট্রেইন
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# মডেল সেভ
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/flood_model.pkl")

print("✅ Model trained successfully and saved to model/flood_model.pkl")
