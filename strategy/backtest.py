import backtrader as bt
import pandas as pd
import os
from backtrader.feeds import PandasData
from .moving_average_strategy import MovingAverageStrategy  # Import the strategy

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
cerebro.addstrategy(MovingAverageStrategy)

# Add the data feed
cerebro.adddata(data_feed)

# Run the backtest
cerebro.run()

# Plot the results
cerebro.plot()
