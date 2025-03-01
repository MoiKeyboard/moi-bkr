import backtrader as bt
import pandas as pd
import os
from backtrader.feeds import PandasData
from strategy.strategies import MovingAverageStrategy  # Import the strategy
from strategy.strategies import ATRMovingAverageStrategy  # Import the strategy

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

# Add the Moving Average strategy
# cerebro.addstrategy(MovingAverageStrategy)
cerebro.addstrategy(ATRMovingAverageStrategy)

# Add the data feed
cerebro.adddata(data_feed)

# Add performance analyzers
cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")

# Run the backtest
results = cerebro.run()

# Extract and print performance metrics
sharpe_ratio = results[0].analyzers.sharpe.get_analysis()
drawdown = results[0].analyzers.drawdown.get_analysis()
returns = results[0].analyzers.returns.get_analysis()
trades = results[0].analyzers.trades.get_analysis()
# timereturn = results[0].analyzers.timereturn.get_analysis()

# performance metrics
print("\nPerformance Metrics:")
print(f"Sharpe Ratio: {sharpe_ratio['sharperatio']}")
print(f"Max Drawdown: {drawdown['max']['drawdown']}%")
print(f"Annual Return: {returns['rnorm100']}%")  # Annualized return in percentage
print(f"Total Return: {returns['rtot']}")  # Total return over the entire period

# Trade Analysis
print("\nTrade Analysis:")
print(f"Total Trades: {trades['total']['total']}")
print(f"Winning Trades: {trades['won']['total']}")
print(f"Losing Trades: {trades['lost']['total']}")
print(f"Win Rate: {trades['won']['total'] / trades['total']['total'] * 100:.2f}%")
print(f"Average Win: {trades['won']['pnl']['average']}")
print(f"Average Loss: {trades['lost']['pnl']['average']}")
print(f"Profit Factor: {trades['pnl']['net']['total']} / {abs(trades['pnl']['net']['total'] - trades['won']['pnl']['total'])}")

# Plot the results
# cerebro.plot()