import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.metrics import mean_squared_error, r2_score
from ta.momentum import RSIIndicator
from ta.trend import MACD

# Load the data
df = pd.read_csv("btc_data50days.csv")

# Convert timestamp to datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# Sort by time just in case
df.sort_values('Timestamp', inplace=True)

# Feature Engineering
df['return'] = df['Close'].pct_change()
df['prev_close'] = df['Close'].shift(1)
df['rolling_mean'] = df['Close'].rolling(window=5).mean()
df['rolling_std'] = df['Close'].rolling(window=5).std()

# Add RSI
df['rsi'] = RSIIndicator(close=df['Close'], window=14).rsi()

# Add MACD
macd = MACD(close=df['Close'])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()
df['macd_diff'] = macd.macd_diff()

# Target: next close
df['next_close'] = df['Close'].shift(-1)

# Drop rows with NaNs (from rolling, shift, etc.)
df.dropna(inplace=True)

# Select features and target
features = [
    'prev_close', 'return',
    'rolling_mean', 'rolling_std',
    'rsi', 'macd', 'macd_signal', 'macd_diff'
]
X = df[features]
y = df['next_close']

# Time-based split (80% train, 20% test)
split = int(len(df) * 0.8)
x_train, x_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

# XGBoost model with regularization
model = xgb.XGBRegressor(
    n_estimators=300,
    max_depth=3,                # ⬇️ Lower depth for stability
    learning_rate=0.05,         # ⬇️ Lower learning rate
    subsample=0.7,
    colsample_bytree=0.7,
    reg_alpha=0.5,              # L1 regularization
    reg_lambda=1.0,             # L2 regularization
    early_stopping_rounds=20,
    random_state=42
)

# Fit with evaluation set
model.fit(
    x_train, y_train,
    eval_set=[(x_test, y_test)],
    verbose=False
)

# Predict
y_pred = model.predict(x_test)

# Evaluate
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
print(f"MSE: {mse:.2f}, R2 Score: {r2:.4f}")

# Plot predictions vs actual
plt.figure(figsize=(12, 6))
plt.plot(y_test.values[:300], label='Actual')
plt.plot(y_pred[:300], label='Predicted')
plt.title("XGBoost Prediction vs Actual (First 300 Points)")
plt.xlabel("Time")
plt.ylabel("Price")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

