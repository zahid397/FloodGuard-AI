import pandas as pd
import numpy as np

def preprocess_data(df):
    """
    Clean and prepare flood data.
    """
    # Fill missing values with mean
    numeric_cols = ['rainfall', 'humidity', 'temperature', 'river_level', 'pressure']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].mean())

    # Normalization (Min-Max scaler)
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    # If no flood_risk, create dummy (for demo)
    if 'flood_risk' not in df.columns:
        df['flood_risk'] = np.where(df['rainfall'] > 0.7, 1, 0)  # Threshold-based dummy

    # Date to datetime if present
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    print(f"Preprocessed data shape: {df.shape}")
    return df
