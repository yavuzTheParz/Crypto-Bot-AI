import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.metrics import mean_squared_error, r2_score

# Load and prepare data
df = pd.read_csv('btc_data_1week.csv')

# Feature engineering
df['prev_close'] = df['Close'].shift(1)
df['return'] = df['Close'].pct_change()
df['rolling_mean'] = df['Close'].rolling(window=5).mean()
df['rolling_std'] = df['Close'].rolling(window=5).std()

# Drop NaN values caused by shifting and rolling
df.dropna(inplace=True)

# Select features
features = ['Close', 'prev_close', 'return', 'rolling_mean', 'rolling_std']
data = df[features].values

# Normalize features
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(data)

# Create sequences
def create_sequences(data, seq_length):
    x, y = [], []
    for i in range(len(data) - seq_length):
        x.append(data[i:i + seq_length])
        y.append(data[i + seq_length][0])  # Predict only the 'Close' price
    return np.array(x), np.array(y)

seq_length = 60
train_size = int(len(scaled_data) * 0.8)

train_data = scaled_data[:train_size]
test_data = scaled_data[train_size:]

x_train, y_train = create_sequences(train_data, seq_length)
x_test, y_test = create_sequences(test_data, seq_length)

# Build model input shape
x_train = x_train.reshape((x_train.shape[0], x_train.shape[1], x_train.shape[2]))
x_test = x_test.reshape((x_test.shape[0], x_test.shape[1], x_test.shape[2]))

# Build LSTM model
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], x_train.shape[2])))
model.add(LSTM(units=50, return_sequences=False))
model.add(Dense(units=1))

model.compile(optimizer='adam', loss='mean_squared_error')

# Train model
model.fit(x_train, y_train, epochs=10, batch_size=32)

# Predict and inverse transform the 'Close' value only
predicted_data = model.predict(x_test)

# To inverse transform only the Close column, build dummy full-size arrays
full_pred = np.zeros((predicted_data.shape[0], scaled_data.shape[1]))
full_pred[:, 0] = predicted_data[:, 0]  # Set only the 'Close' column

full_y_test = np.zeros((y_test.shape[0], scaled_data.shape[1]))
full_y_test[:, 0] = y_test

predicted_close = scaler.inverse_transform(full_pred)[:, 0]
actual_close = scaler.inverse_transform(full_y_test)[:, 0]

# Evaluate
r2 = r2_score(actual_close, predicted_close)
mse = mean_squared_error(actual_close, predicted_close)
print(f'MSE: {mse:.2f}, R2 Score: {r2:.4f}')

# Save model
model.save('lstm_model_with_features.h5')

# Plot
plt.figure(figsize=(12, 6))
plt.plot(actual_close[:500], label='Actual')
plt.plot(predicted_close[:500], label='Predicted')
plt.legend()
plt.title("Zoomed-In Prediction vs Actual (First 500 Points)")
plt.xlabel("Time Steps")
plt.ylabel("BTC Price")
plt.show()
