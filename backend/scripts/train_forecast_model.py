import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
from pathlib import Path
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.multioutput import MultiOutputRegressor

DATA_DIR = Path(__file__).parent.parent / "data"
MODEL_PATH = DATA_DIR / "pea_lgbm_model.pkl"

def train_model():
    input_file = DATA_DIR / "training_set.csv"
    if not input_file.exists():
        print(f"❌ Error: {input_file} not found.")
        return

    print(f"Loading dataset: {input_file}")
    df = pd.read_csv(input_file, index_col='datetime', parse_dates=['datetime'])
    
    # Feature columns (as preprocessed)
    features = [
        'irradiance', 'temp_c', 'humidity', 'hour', 'day_of_week', 'month', 
        'is_weekend', 'hour_sin', 'hour_cos', 'load_lag_1h', 'load_lag_2h', 'load_lag_24h'
    ]
    
    # We want to predict South Demand (Load) and South Generation (Proxy for Capacity)
    targets = ['south_demand', 'south_generation']
    
    X = df[features]
    y = df[targets]
    
    # Manual Time-Series Split (Last 1000 hours for testing)
    test_size = 1000
    X_train, X_test = X.iloc[:-test_size], X.iloc[-test_size:]
    y_train, y_test = y.iloc[:-test_size], y.iloc[-test_size:]
    
    print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")
    
    # Define LightGBM base regressor
    base_lgbm = lgb.LGBMRegressor(
        objective='regression',
        metric='rmse',
        verbosity=-1,
        boosting_type='gbdt',
        num_leaves=31,
        learning_rate=0.05,
        feature_fraction=0.9,
        n_estimators=500
    )
    
    # Wrap in MultiOutputRegressor to handle both Demand and Generation simultaneously
    multi_model = MultiOutputRegressor(base_lgbm)
    
    print("🤖 Training Hybrid AI Forecasting Model...")
    multi_model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = multi_model.predict(X_test)
    mape_load = mean_absolute_percentage_error(y_test['south_demand'], y_pred[:, 0])
    mape_gen = mean_absolute_percentage_error(y_test['south_generation'], y_pred[:, 1])
    
    print(f"\n📊 Performance (MAPE):")
    print(f"   Load MAPE:     {mape_load * 100:.2f}% {'✅' if mape_load < 0.1 else '⚠️'}")
    print(f"   Generation MAPE: {mape_gen * 100:.2f}% {'✅' if mape_gen < 0.1 else '⚠️'}")
    
    # Save the MultiOutputRegressor
    joblib.dump(multi_model, MODEL_PATH)
    print(f"✅ Success! Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
