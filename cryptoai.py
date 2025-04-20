import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import RobustScaler
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

# Load and prepare data
df = pd.read_csv('btc_data_1week.csv')
df['prev_close'] = df['Close'].shift(1)
df['prev_return'] = df['Close'].pct_change()
df['rolling_mean'] = df['Close'].rolling(window=5).mean()
df['rolling_std'] = df['Close'].rolling(window=5).std()  # Removes NaNs caused by shifting/rolling
df.dropna(inplace=True)


y = df['Close'].shift(-1).dropna()  # Shift and remove the last NaN row from the target

# Features
features = ['Open', 'High', 'Low', 'Volume', 'prev_close', 'prev_return', 'rolling_mean', 'rolling_std']
df = df.iloc[:-1]  # Drop the last row from the dataframe to align with y

# Ensure no NaN values in features
df.dropna(inplace=True)

x = df[features]


split_index = int(len(df) * 0.8)
x_train, x_test = x.iloc[:split_index], x.iloc[split_index:]
y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]


# Model
model = XGBRegressor(eval_metric='rmse', max_depth=6, learning_rate=0.1, n_estimators=100)
model.fit(x_train, y_train)
model.save_model('xgb_model.json')  
y_pred = model.predict(x_test)
#metric
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f'MSE: {mse:.2f}, R2 Score: {r2:.4f}')

#plot
plt.figure(figsize=(12, 6))
plt.plot(y_test.values[:500], label='Actual')
plt.plot(y_pred[:500], label='Predicted')
plt.legend()
plt.title("Zoomed-In Prediction vs Actual (First 500 Points)")
plt.show()

plt.hist(df['next_close'], bins=100)
plt.title('Distribution of Target Values')
plt.show()






