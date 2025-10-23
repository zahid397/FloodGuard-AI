import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error
import joblib
import os

# ডেটা লোড
df = pd.read_csv("flood_data_clean.csv")

# ইনপুট ফিচার এবং টার্গেট সিলেক্ট
X = df[['Avg_Temperature_C', 'Annual_Rainfall_mm', 'AQI', 'Forest_Cover_Percent',
        'River_Water_Level_m', 'Cyclone_Count', 'Drought_Severity',
        'Agricultural_Yield_ton_per_hectare', 'Coastal_Erosion_m_per_year',
        'Urbanization_Rate_Percent', 'Carbon_Emission_Metric_Tons_per_Capita',
        'Renewable_Energy_Usage_Percent']]
y = df['Flood_Impact_Score']

# ট্রেইন টেস্ট স্প্লিট
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# মডেল তৈরি
model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

# প্রেডিকশন এবং পারফরম্যান্স মেট্রিক
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)

print(f"✅ Model Trained Successfully!")
print(f"📊 R² Score: {r2:.3f}")
print(f"📉 Mean Squared Error: {mse:.3f}")

# মডেল ফোল্ডার তৈরি করে সেভ করা
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/flood_model.pkl")
print("💾 Model saved as 'model/flood_model.pkl'")
