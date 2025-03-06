import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
import pytz

from .base_provider import DataProvider

class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider implementation."""
    
    def __init__(self):
        """Initialize the Yahoo Finance provider."""
        self.ny_tz = pytz.timezone('America/New_York')
    
    def fetch_data(self, tickers: List[str], lookback_period: int) -> Dict[str, pd.DataFrame]:
        """Fetch historical market data from Yahoo Finance."""
        data = {}
        for ticker in tickers:
            try:
                df = yf.Ticker(ticker).history(period=f"{lookback_period}d")
                if not df.empty:
                    data[ticker] = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        return data
    
    def is_market_open(self) -> bool:
        """
        Check if US market is currently open.
        
        Returns:
            bool: True if market is open, False otherwise
        """
        now = datetime.now(self.ny_tz)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            return False
            
        # Convert to time object
        current_time = now.time()
        
        # Regular market hours (9:30 AM - 4:00 PM Eastern)
        market_open = datetime.strptime("9:30", "%H:%M").time()
        market_close = datetime.strptime("16:00", "%H:%M").time()
        
        return market_open <= current_time <= market_close
    
    def get_trading_hours(self) -> Dict:
        """
        Get US market trading hours.
        
        Returns:
            Dict with market hours information
        """
        return {
            'market_open': '9:30',
            'market_close': '16:00',
            'timezone': 'America/New_York',
            'pre_market_open': '4:00',
            'after_market_close': '20:00'
        }