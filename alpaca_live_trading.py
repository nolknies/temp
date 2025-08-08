import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

# Set your Alpaca API credentials
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_API_SECRET")

# Trading client for orders, positions
trading_client = TradingClient(API_KEY, API_SECRET, paper=True)  # paper=True for paper trading

# Market data client for price data
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

# Your GitHub raw CSV URL for latest signals
CSV_URL = "https://raw.githubusercontent.com/nolknies/temp/main/stock_signals.csv"

def fetch_signals():
    resp = requests.get(CSV_URL)
    df = pd.read_csv(io.StringIO(resp.text))
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y').dt.date
    return df

def get_latest_price(symbol):
    try:
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe="1Day",
            limit=1
        )
        bars = data_client.get_stock_bars(request_params)
        if bars and symbol in bars and len(bars[symbol]) > 0:
            return bars[symbol][0].c  # close price of latest bar
        else:
            print(f"No price data for {symbol}")
            return None
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

def trade_on_signals():
    signals_df = fetch_signals()
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Filter signals for yesterday
    signals_yesterday = signals_df[signals_df['Date'] == yesterday]
    
    if signals_yesterday.empty:
        print(f"No signals for {yesterday}, skipping trades")
        return
    
    positions = {pos.symbol: pos for pos in trading_client.get_all_positions()}
    
    for _, row in signals_yesterday.iterrows():
        symbol = row['Ticker']
        signal = int(row['PredictedSignal'])
        
        current_position = positions.get(symbol)
        is_invested = current_position is not None
        
        price = get_latest_price(symbol)
        if price is None:
            continue
        
        # Buy if signal=1 and not invested
        if signal == 1 and not is_invested:
            qty = int(1000 // price)  # Buy approx $1000 worth (adjust as needed)
            if qty == 0:
                print(f"Qty zero for {symbol} at price {price}, skipping buy")
                continue
            
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            order = trading_client.submit_order(order_data)
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
            order = trading_client.submit_order(order_data)
            print(f"SELL order submitted for {symbol}: qty {qty}")

if __name__ == "__main__":
    trade_on_signals()

