import numpy as np
import pandas as pd
from binance.client import Client
from ta.momentum import RSIIndicator
from ta.trend import MACD
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
import time

# === Binance API credentials ===
API_KEY = 'gN9ATvZT4JivfsIpDK6bifR0aVDzZGXnbyBQed92wqmSlYbSCsFTF3eW7K5kvmwG'
API_SECRET = 'FqB27GDn5aioaErhNKauBlBi8r4dKPpnOJgCbxGv4jodiMvvvwVO3Yr04iP3Y55z'
client = Client(API_KEY, API_SECRET)

# === Model & trading parameters ===
MODEL_PATH = 'lstm_model_with_indicators.h5'
symbol = 'BTCUSDT'
interval = '1m'  # 1-minute intervals for real-time simulation
seq_length = 60  # 60 minutes of historical data for prediction
CASH_AT_RISK_BUY = 0.05  # 5% of USDT balance for BUY
CASH_AT_RISK_SELL = 0.10  # 10% of BTC balance for SELL

# === Load model ===
model = load_model(MODEL_PATH)

# === Initialize Paper Wallet ===
paper_wallet = {
    'usdt': 100.0,  # Start with 10,000 USDT
    'btc': 0.0,
    'trades': [],
    'initial_balance': 10000.0
}

# === Data retrieval (fetch live data) ===
def get_binance_data(symbol, interval, limit=200):
    klines = client.get_historical_klines(symbol, interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close_time', 'Quote_asset_volume', 'Number_of_trades',
        'Taker_buy_base_vol', 'Taker_buy_quote_vol', 'Ignore'
    ])
    df['Close'] = df['Close'].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# === Preprocess data for model ===
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

    return df, X_scaled

# === Decision Logic with Dynamic Threshold ===
def decide_action(current_price, predicted_price, recent_vol):
    threshold = recent_vol / current_price
    diff = (predicted_price - current_price) / current_price

    if diff > threshold:
        return 'BUY'
    elif diff < -threshold:
        return 'SELL'
    else:
        return 'HOLD'

# === Simulate Trade Execution ===
def simulate_trade(action, current_price):
    usdt = paper_wallet['usdt']
    btc = paper_wallet['btc']
    log = paper_wallet['trades']

    if action == 'BUY':
        cash_to_use = usdt * CASH_AT_RISK_BUY
        quantity = round(cash_to_use / current_price, 6)

        if cash_to_use >= 10:
            paper_wallet['usdt'] -= quantity * current_price
            paper_wallet['btc'] += quantity
            log.append(f"BUY {quantity:.6f} BTC at {current_price:.2f}")
        else:
            log.append("BUY skipped — not enough USDT")

    elif action == 'SELL':
        quantity = round(btc * CASH_AT_RISK_SELL, 6)

        if quantity * current_price >= 10:
            paper_wallet['btc'] -= quantity
            paper_wallet['usdt'] += quantity * current_price
            log.append(f"SELL {quantity:.6f} BTC at {current_price:.2f}")
        else:
            log.append("SELL skipped — not enough BTC")

    else:
        log.append("HOLD")

# === Portfolio Performance ===
def print_portfolio(current_price):
    total_value = paper_wallet['usdt'] + paper_wallet['btc'] * current_price
    pnl = total_value - paper_wallet['initial_balance']
    print(f"[PORTFOLIO] USDT: {paper_wallet['usdt']:.2f}, BTC: {paper_wallet['btc']:.6f}, Total: {total_value:.2f}, PnL: {pnl:.2f}")

# === Run simulation for real-time paper trading ===
def run_real_time_simulation():
    while True:
        # Fetch latest market data
        df_raw = get_binance_data(symbol, interval)
        df, X_scaled = preprocess_data(df_raw)

        # Get the last minute data point
        current_price = df['Close'].iloc[-1]
        recent_vol = df['volatility'].iloc[-1]

        # Get model prediction
        x_input = np.expand_dims(X_scaled[-seq_length:], axis=0)
        predicted_scaled = model.predict(x_input, verbose=0)
        predicted_price = predicted_scaled[0][0] * current_price  # approximate scaling

        # Make decision based on model prediction
        action = decide_action(current_price, predicted_price, recent_vol)

        # Simulate the trade
        simulate_trade(action, current_price)

        # Print portfolio and decision
        print(f"[{df['timestamp'].iloc[-1]}] Current: {current_price:.2f}, Predicted: {predicted_price:.2f}, Action: {action}")
        print_portfolio(current_price)
        print('-' * 60)

        # Sleep for the next minute
        time.sleep(60)  # Adjust for the interval (e.g., 1 minute)

# === Run the simulation ===
if __name__ == '__main__':
    run_real_time_simulation()

