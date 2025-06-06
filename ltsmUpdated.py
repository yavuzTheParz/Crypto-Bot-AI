	mport pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from ta.momentum import RSIIndicator
from ta.trend import MACD

# Load data
df = pd.read_csv('btc_data.csv')

# Feature Engineering
df['prev_close'] = df['Close'].shift(1)
df['return'] = df['Close'].pct_change()
df['rolling_mean'] = df['Close'].rolling(window=5).mean()
df['rolling_std'] = df['Close'].rolling(window=5).std()

# Add RSI
df['rsi'] = RSIIndicator(close=df['Close'], window=14).rsi()

# Add MACD
macd = MACD(close=df['Close'])
df['macd'] = macd.macd()
df['macd_signal'] = macd.macd_signal()
df['macd_diff'] = macd.macd_diff()

# Target: next_close
df['next_close'] = df['Close'].shift(-1)

# Drop rows with NaNs
df.dropna(inplace=True)

# Select features and target
features = [
    'prev_close', 'return',
    'rolling_mean', 'rolling_std',
    'rsi', 'macd', 'macd_signal', 'macd_diff'
]
target = 'next_close'

# Prepare data
X = df[features].values
y = df[target].values.reshape(-1, 1)

# Normalize
scaler_X = MinMaxScaler()
X_scaled = scaler_X.fit_transform(X)

scaler_y = MinMaxScaler()
y_scaled = scaler_y.fit_transform(y)

# Create sequences
def create_sequences(X, y, seq_length):
    x_seq, y_seq = [], []
    for i in range(len(X) - seq_length):
        x_seq.append(X[i:i + seq_length])
        y_seq.append(y[i + seq_length])
    return np.array(x_seq), np.array(y_seq)

seq_length = 60
train_size = int(len(X_scaled) * 0.8)

x_train, y_train = create_sequences(X_scaled[:train_size], y_scaled[:train_size], seq_length)
x_test, y_test = create_sequences(X_scaled[train_size:], y_scaled[train_size:], seq_length)

# Build LSTM model
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], x_train.shape[2])))
model.add(LSTM(units=50))
model.add(Dense(units=1))

model.compile(optimizer='adam', loss='mean_squared_error')

# Early stopping
early_stop = EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)

# Train the model with validation split
history = model.fit(
    x_train, y_train,
    epochs=100,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1,
    validation_split=0.2  # Use 20% of the training data as validation
)

# Predict
predicted_scaled = model.predict(x_test)
predicted = scaler_y.inverse_transform(predicted_scaled)
actual = scaler_y.inverse_transform(y_test)

# Evaluate the model
r2 = r2_score(actual, predicted)
mse = mean_squared_error(actual, predicted)
mae = mean_absolute_error(actual, predicted)

print(f'MSE: {mse:.2f}, R2 Score: {r2:.4f}, MAE: {mae:.2f}')

# Save the best model
model.save('lstm_model_with_indicators_best.h5')

# Plot Prediction vs Actual
plt.figure(figsize=(12, 6))
plt.plot(actual[:500], label='Actual')
plt.plot(predicted[:500], label='Predicted')
plt.legend()
plt.title("Prediction vs Actual (First 500 Points)")
plt.xlabel("Time Steps")
plt.ylabel("BTC Price")
plt.show()

# Plot Training Loss
plt.figure(figsize=(8, 4))
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Training and Validation Loss Over Epochs')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.show()

