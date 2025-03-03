from tws.tws_client import TWSClient
from tws.historical_data import HistoricalData
from ib_insync import Stock

# Connect to TWS
tws = TWSClient(host="host.docker.internal", port=7497)
tws.connect()

try:
    # Create historical data client
    hist_client = HistoricalData(tws)

    # Define the contract for AAPL
    aapl_contract = Stock("AAPL", "SMART", "USD")

    # Fetch historical data for AAPL
    aapl_data = hist_client.get_historical_data(
        aapl_contract,
        duration="1 Y",  # Fetch data for the past year
        bar_size="1 day",  # Daily bars
    )

    # Save the data to a CSV file
    hist_client.save_historical_data(
        aapl_contract, filename="strategy/historical_prices.csv"
    )

    print(f"Downloaded {len(aapl_data)} bars of AAPL data")

finally:
    # Always disconnect
    tws.disconnect()
