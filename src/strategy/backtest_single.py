import backtrader as bt
import pandas as pd
import os
from backtrader.feeds import PandasData
from src.strategy.strategies import (
    MovingAverageStrategy,
    ATRMovingAverageStrategy,
    VWAPStrategy,
    ATRVWAPStrategy,
    SmartTrendStrategy,
)

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the CSV file
csv_path = os.path.join(script_dir, "historical_prices.csv")

# Load historical stock data
data = pd.read_csv(csv_path)

# Convert the 'Date' column to datetime format
data["Date"] = pd.to_datetime(data["Date"], format="%Y-%m-%d")

# Set the 'Date' column as the index
data.set_index("Date", inplace=True)

# Rename columns if necessary (ensure compatibility with Backtrader)
data.rename(columns={"Adj Close": "Close"}, inplace=True)

# Create the data feed for Backtrader
data_feed = PandasData(dataname=data)

# Initialize Backtrader engine
cerebro = bt.Cerebro()

# Choose which strategy to use (uncomment one)
# cerebro.addstrategy(MovingAverageStrategy)
# cerebro.addstrategy(ATRMovingAverageStrategy)
# cerebro.addstrategy(VWAPStrategy)
# cerebro.addstrategy(ATRVWAPStrategy)
cerebro.addstrategy(SmartTrendStrategy)  # Using the new strategy

# Add the data feed
cerebro.adddata(data_feed)

# Set initial cash
cerebro.broker.setcash(100000.0)  # Start with 100k

# Add performance analyzers
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")

# Run the backtest
print("\nStarting Portfolio Value: %.2f" % cerebro.broker.getvalue())
results = cerebro.run()
print("Final Portfolio Value: %.2f" % cerebro.broker.getvalue())

# Extract and print performance metrics
strat = results[0]
sharpe_ratio = strat.analyzers.sharpe.get_analysis()
drawdown = strat.analyzers.drawdown.get_analysis()
returns = strat.analyzers.returns.get_analysis()
trades = strat.analyzers.trades.get_analysis()

# Print performance summary
print("\nPerformance Metrics:")
print(f"Sharpe Ratio: {sharpe_ratio['sharperatio']:.2f}")
print(f"Max Drawdown: {drawdown['max']['drawdown']:.2%}")
print(f"Total Return: {returns['rtot']:.2%}")

# Trade Analysis
print("\nTrade Analysis:")
print(f"Total Trades: {trades['total']['total']}")
print(f"Winning Trades: {trades['won']['total']}")
print(f"Losing Trades: {trades['lost']['total']}")
win_rate = trades["won"]["total"] / trades["total"]["total"] * 100
print(f"Win Rate: {win_rate:.2f}%")
print(f"Average Win: {trades['won']['pnl']['average']:.2f}")
print(f"Average Loss: {trades['lost']['pnl']['average']:.2f}")

# Calculate profit factor
net_profit = trades["pnl"]["net"]["total"]
gross_loss = abs(trades["pnl"]["net"]["total"] - trades["won"]["pnl"]["total"])
print(f"Profit Factor: {net_profit:.2f} / {gross_loss:.2f}")

# Plot the results
# cerebro.plot(style='candlestick')
