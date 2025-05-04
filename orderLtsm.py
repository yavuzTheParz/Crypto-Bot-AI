	mport numpy as np
import pandas as pd
from binance.client import Client
from binance.enums import *
from ta.momentum import RSIIndicator
from ta.trend import MACD
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
import datetime
import time

# === Binance API credentials ===
API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'
client = Client(API_KEY, API_SECRET)

# === Model & trading parameters ===
MODEL_PATH = 'lstm_model_with_indicators.h5'
symbol = 'BTCUSDT'
interval = '1h'
lookback = '200 hours'
seq_length = 60

CASH_AT_RISK_BUY = 0.05   # 5% of USDT balance for BUY
CASH_AT_RISK_SELL = 0.10  # 10% of BTC balance for SELL
MIN_ORDER_VALUE = 10      # Binance minimum order value

# === Load trained model ===
model = load_model(MODEL_PATH)

# === Data retrieval and preprocessing ===
def get_binance_data(symbol, interval, lookback):
    klines = client.get_historical_klines(symbol, interval, lookback)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close_time', 'Quote_asset_volume', 'Number_of_trades',
        'Taker_buy_base_vol', 'Taker_buy_quote_vol', 'Ignore'
    ])
    df['Close'] = df['Close'].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def preprocess_data(df):
    df['prev_close'] = df['Close'].shift(1)
    df['return'] = df['Close'].pct_change()
    df['rolling_mean'] = df['Close'].rolling(window=5).mean()
    df['rolling_std'] = df['Close'].rolling(window=5).std()
    df['volatility'] = df['Close'].rolling(window=20).std()
    df['rsi'] = RSIIndicator(close=df['Close'], window=14).rsi()
    macd = MACD(close=df['Close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()
    df.dropna(inplace=True)

    features = ['prev_close', 'return', 'rolling_mean', 'rolling_std', 'rsi', 'macd', 'macd_signal', 'macd_diff']
    X = df[features].values

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    x_input = np.expand_dims(X_scaled[-seq_length:], axis=0)
    current_price = df['Close'].iloc[-1]
    recent_vol = df['volatility'].iloc[-1]

    return x_input, current_price, recent_vol

# === Trade decision logic ===
def decide_action(current_price, predicted_price, recent_vol):
    threshold = recent_vol / current_price  # Dynamic threshold
    diff = (predicted_price - current_price) / current_price

    print(f"[THRESHOLD] Dynamic Threshold: {threshold:.4f}, Diff: {diff:.4f}")

    if diff > threshold:
        return 'BUY'
    elif diff < -threshold:
        return 'SELL'
    else:
        return 'HOLD'

# === Balance check ===
def get_balances():
    balances = client.get_account()['balances']
    usdt = float(next(b['free'] for b in balances if b['asset'] == 'USDT'))
    btc = float(next(b['free'] for b in balances if b['asset'] == 'BTC'))
    return usdt, btc

# === Trade execution ===
def execute_trade(action, current_price):
    usdt_balance, btc_balance = get_balances()
    print(f"[BALANCE] USDT: {usdt_balance:.2f}, BTC: {btc_balance:.6f}, Price: {current_price:.2f}")

    if action == 'BUY':
        quantity = (usdt_balance * CASH_AT_RISK_BUY) / current_price
        quantity = round(quantity, 6)
        order_value = quantity * current_price

        if order_value < MIN_ORDER_VALUE:
            print("[BUY] Insufficient USDT to place order.")
            return

        order = client.order_market_buy(symbol=symbol, quantity=quantity)
        print(f"[BUY] Executed: {quantity} BTC (~{order_value:.2f} USDT)")

    elif action == 'SELL':
        quantity = btc_balance * CASH_AT_RISK_SELL
        quantity = round(quantity, 6)
        order_value = quantity * current_price

        if order_value < MIN_ORDER_VALUE:
            print("[SELL] Insufficient BTC to place order.")
            return

        order = client.order_market_sell(symbol=symbol, quantity=quantity)
        print(f"[SELL] Executed: {quantity} BTC (~{order_value:.2f} USDT)")

    else:
        print("[HOLD] No action taken.")

# === Main trading logic ===
def run():
    df = get_binance_data(symbol, interval, lookback)
    x_input, current_price, recent_vol = preprocess_data(df)

    predicted_scaled = model.predict(x_input)
    predicted_price = predicted_scaled[0][0] * current_price  # Approximate inverse scaling

    action = decide_action(current_price, predicted_price, recent_vol)
    print(f"[DECISION] Current: {current_price:.2f}, Predicted: {predicted_price:.2f}, Action: {action}")

    execute_trade(action, current_price)

# === Run script once (or loop it) ===
if __name__ == '__main__':
    run()

    # For continuous trading every hour:
    # while True:
    #     run()
    #     time.sleep(3600)

