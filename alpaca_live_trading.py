import os
import pandas as pd
import requests
import io
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_API_SECRET")
client = TradingClient(API_KEY, API_SECRET, paper=True)  # Use paper trading

CSV_URL = "https://raw.githubusercontent.com/nolknies/temp/main/stock_signals.csv"

def fetch_signals():
    resp = requests.get(CSV_URL)
    df = pd.read_csv(io.StringIO(resp.text))  # Or use io.StringIO
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y').dt.date
    return df

def trade_on_signals():
    signals_df = fetch_signals()
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    signals_yesterday = signals_df[signals_df['Date'] == yesterday]

    if signals_yesterday.empty:
        print(f"No signals for {yesterday}")
        return

    # Get current positions for quick lookup
    positions = {pos.symbol: pos for pos in client.get_all_positions()}

    for _, row in signals_yesterday.iterrows():
        symbol = row['Ticker']
        signal = int(row['PredictedSignal'])
        invested = symbol in positions

        if signal == 1 and not invested:
            # Buy 10 shares (or whatever fixed amount)
            order = MarketOrderRequest(
                symbol=symbol,
                qty=10,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            client.submit_order(order)
            print(f"Placed BUY order for {symbol}")

        elif signal == 0 and invested:
            qty = abs(int(positions[symbol].qty))
            order = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            client.submit_order(order)
            print(f"Placed SELL order for {symbol}")

if __name__ == "__main__":
    trade_on_signals()


if __name__ == "__main__":
    trade_on_signals()

