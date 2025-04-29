	mport numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
import datetime
import time

# === Model & trading parameters ===
MODEL_PATH = 'lstm_model_with_indicators.h5'
symbol = 'BTCUSDT'
interval = '1h'
lookback = '200 hours'
seq_length = 60

CASH_AT_RISK_BUY = 0.05   # 5% of USDT for BUY
CASH_AT_RISK_SELL = 0.10  # 10% of BTC for SELL

# === Load model ===
model = load_model(MODEL_PATH)

# === Initialize Paper Wallet ===
paper_wallet = {
    'usdt': 10000.0,
    'btc': 0.0,
    'trades': [],
    'initial_balance': 10000.0
}

# === Data retrieval (simulate Binance API) ===
def get_data():
    df = pd.read_csv('btc_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# === Preprocess for model input ===
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

# === Run simulation over historical data ===
def run_simulation():
    df_raw = get_data()
    df, X_scaled = preprocess_data(df_raw)

    for i in range(seq_length, len(df)):
        x_input = np.expand_dims(X_scaled[i - seq_length:i], axis=0)
        current_price = df['Close'].iloc[i]
        recent_vol = df['volatility'].iloc[i]

        predicted_scaled = model.predict(x_input, verbose=0)
        predicted_price = predicted_scaled[0][0] * current_price  # approximate scaling

        action = decide_action(current_price, predicted_price, recent_vol)
        simulate_trade(action, current_price)

        print(f"[{df['timestamp'].iloc[i]}] Current: {current_price:.2f}, Predicted: {predicted_price:.2f}, Action: {action}")
        print_portfolio(current_price)
        print('-' * 60)

    # Final Summary
    print("\n=== FINAL RESULTS ===")
    print_portfolio(current_price)
    print("\nTrade Log:")
    for t in paper_wallet['trades']:
        print(t)

# === Run it ===
if __name__ == '__main__':
    run_simulation()

