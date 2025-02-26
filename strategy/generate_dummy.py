import os
import pandas as pd
import numpy as np

# Parameterize the number of days
num_days = 364  # Default to 364 days

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the CSV file
csv_path = os.path.join(script_dir, "historical_prices.csv")

# Generate fake stock data
dates = pd.date_range(start="2023-01-01", periods=num_days, freq="D")
prices = 100 + np.cumsum(np.random.randn(num_days))  # Random walk price data

# Create a DataFrame
df = pd.DataFrame({
    "Date": dates,
    "Open": prices + np.random.randn(num_days),
    "High": prices + np.random.randn(num_days),
    "Low": prices - np.random.randn(num_days),
    "Close": prices,
    "Volume": np.random.randint(100000, 500000, size=num_days)
})

# Set the 'Date' column as the index
df.set_index("Date", inplace=True)

# Save the DataFrame to a CSV file
df.to_csv(csv_path)

print(f"Generated {num_days} days of fake stock data and saved to {csv_path}")