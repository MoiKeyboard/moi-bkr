from typing import List, Dict
import pandas as pd
from datetime import datetime
import pytz
from ib_insync import Stock, IB

from .base_provider import DataProvider


class IBDataProvider(DataProvider):
    """Interactive Brokers data provider implementation."""

    def __init__(self, host: str, port: int, client_id: int):
        """Initialize IB connection settings."""
        super().__init__()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.logger.info(f"Initialized IB provider with host={host}, port={port}")
        self.ny_tz = pytz.timezone("America/New_York")

    def connect(self):
        """Connect to TWS/Gateway."""
        if not self.ib.isConnected():
            self.ib.connect(self.host, self.port, clientId=self.client_id)

    def disconnect(self):
        """Disconnect from TWS/Gateway."""
        if self.ib.isConnected():
            self.ib.disconnect()

    def fetch_data(
        self, tickers: List[str], lookback_period: int
    ) -> Dict[str, pd.DataFrame]:
        """Fetch historical market data from Interactive Brokers."""
        self.logger.info(f"Fetching data from Interactive Brokers for {len(tickers)} tickers")
        data = {}
        try:
            self.logger.debug(f"Connecting to TWS at {self.host}:{self.port}")
            self.connect()

            for ticker in tickers:
                try:
                    self.logger.debug(f"Fetching {ticker} data for past {lookback_period} days")
                    contract = Stock(ticker, "SMART", "USD")
                    bars = self.ib.reqHistoricalData(
                        contract,
                        endDateTime="",
                        durationStr=f"{lookback_period} D",
                        barSizeSetting="1 day",
                        whatToShow="TRADES",
                        useRTH=True,
                    )

                    if bars:
                        df = pd.DataFrame(
                            {
                                "Open": [bar.open for bar in bars],
                                "High": [bar.high for bar in bars],
                                "Low": [bar.low for bar in bars],
                                "Close": [bar.close for bar in bars],
                                "Volume": [bar.volume for bar in bars],
                            },
                            index=[bar.date for bar in bars],
                        )
                        data[ticker] = df
                        self.logger.debug(f"Successfully fetched {ticker} data")

                except Exception as e:
                    self.logger.error(f"Error fetching {ticker}: {e}")

        finally:
            if self.ib.isConnected():
                self.logger.debug("Disconnecting from TWS")
                self.disconnect()

        return data

    def is_market_open(self) -> bool:
        """
        Check if US market is currently open.

        Returns:
            bool: True if market is open, False otherwise
        """
        try:
            self.connect()
            # Use IB's market hours data
            return self.ib.marketPrice(Stock("SPY", "SMART", "USD")) > 0
        except:
            # Fallback to time-based check
            now = datetime.now(self.ny_tz)

            if now.weekday() >= 5:
                return False

            current_time = now.time()
            market_open = datetime.strptime("9:30", "%H:%M").time()
            market_close = datetime.strptime("16:00", "%H:%M").time()

            return market_open <= current_time <= market_close
        finally:
            self.disconnect()

    def get_trading_hours(self) -> Dict:
        """
        Get US market trading hours.

        Returns:
            Dict with market hours information
        """
        return {
            "market_open": "9:30",
            "market_close": "16:00",
            "timezone": "America/New_York",
            "pre_market_open": "4:00",
            "after_market_close": "20:00",
        }
