# Stock Trading Project

## Models
### make_predictions.py
  OG model, horizon prediction so signals now one day late beofre placed
### new Claude


## CSVs
### stock_siganls.csv
  Predicted signals using make_predictions.py
### new backtest

### now trading


## Workflows
### alpaca_trade.yml
  Scheduler for alpaca_live_trading.py. Runs every weekday at market open
### update_signals.yml
  Scheduler for make_predictions.py. Refreshes signals in stock_signals.csv (1 day lag)
### new

