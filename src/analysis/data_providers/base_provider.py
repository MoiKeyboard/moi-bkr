from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd


class DataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def fetch_data(
        self, tickers: List[str], lookback_period: int
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical market data for given tickers.

        Args:
            tickers: List of ticker symbols
            lookback_period: Number of days of historical data

        Returns:
            Dict mapping ticker symbols to DataFrames with OHLCV data
        """
        pass

    @abstractmethod
    def is_market_open(self) -> bool:
        """Check if the market is currently open."""
        pass

    @abstractmethod
    def get_trading_hours(self) -> Dict:
        """Get trading hours for the market."""
        pass
