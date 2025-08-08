import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Set your Alpaca API credentials
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_API_SECRET")
BASE_URL = "https://paper-api.alpaca.markets"  # Use paper trading URL

client = TradingClient(API_KEY, API_SECRET, paper=True)

# Your GitHub raw CSV URL for latest signals
CSV_URL = "https://raw.githubusercontent.com/nolknies/temp/main/stock_signals.csv"

def fetch_signals():
    resp = requests.get(CSV_URL)
    df = pd.read_csv(io.StringIO(resp.text))
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y').dt.date
    return df

def trade_on_signals():
    signals_df = fetch_signals()
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Filter signals for yesterday
    signals_yesterday = signals_df[signals_df['Date'] == yesterday]
    
    if signals_yesterday.empty:
        print(f"No signals for {yesterday}, skipping trades")
        return
    
    positions = {pos.symbol: pos for pos in client.get_all_positions()}
    
    for _, row in signals_yesterday.iterrows():
        symbol = row['Ticker']
        signal = int(row['PredictedSignal'])
        
        current_position = positions.get(symbol)
        is_invested = current_position is not None
        
        # Check current price
        try:
            barset = client.get_bars(symbol, limit=1, timeframe="1Day")
            if not barset or not barset[0].c:
                print(f"No price data for {symbol}, skipping")
                continue
            price = barset[0].c
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            continue
        
        # Buy if signal=1 and not invested
        if signal == 1 and not is_invested:
            qty = int(1000 // price)  # Buy approx $1000 worth (adjust as you want)
            if qty == 0:
                print(f"Qty zero for {symbol} at price {price}, skipping buy")
                continue
            
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            order = client.submit_order(order_data)
            print(f"BUY order submitted for {symbol}: qty {qty}")
        
        # Sell if signal=0 and invested
        elif signal == 0 and is_invested:
            qty = abs(int(current_position.qty))
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            order = client.submit_order(order_data)
            print(f"SELL order submitted for {symbol}: qty {qty}")

if __name__ == "__main__":
    trade_on_signals()
