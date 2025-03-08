import backtrader as bt
import numpy as np
import pandas as pd
from typing import Dict


class VWAP(bt.Indicator):
    """
    Custom Volume-Weighted Average Price (VWAP) Indicator.

    VWAP is calculated as:
        VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)

    It is used to determine market trends and fair value.
    """

    alias = ("VWAP",)
    lines = ("vwap",)
    params = dict(period=14)  # Default period

    def __init__(self):
        """Initialize VWAP calculation components."""
        typical_price = (self.data.high + self.data.low + self.data.close) / 3
        volume = self.data.volume

        self.cum_tp_vol = bt.indicators.SumN(
            typical_price * volume, period=self.p.period
        )
        self.cum_vol = bt.indicators.SumN(volume, period=self.p.period)
        self.lines.vwap = self.cum_tp_vol / self.cum_vol


class OBV(bt.Indicator):
    """
    On Balance Volume (OBV) Technical Indicator.

    Formula:
    - If closing price > prior close price then: Current OBV = Previous OBV + Current Volume
    - If closing price < prior close price then: Current OBV = Previous OBV - Current Volume
    - If closing price = prior close price then: Current OBV = Previous OBV
    """

    lines = ("obv",)  # Define the line names
    plotinfo = dict(subplot=True)  # Plot in a separate subplot

    def __init__(self):
        super(OBV, self).__init__()

    def next(self):
        if len(self) <= 1:  # Initialize first value
            self.lines.obv[0] = self.data.volume[0]
            return

        prev_obv = self.lines.obv[-1]

        if self.data.close[0] > self.data.close[-1]:  # Price increased
            self.lines.obv[0] = prev_obv + self.data.volume[0]
        elif self.data.close[0] < self.data.close[-1]:  # Price decreased
            self.lines.obv[0] = prev_obv - self.data.volume[0]
        else:  # Price unchanged
            self.lines.obv[0] = prev_obv


class TechnicalIndicators:
    """Collection of technical indicators for market analysis."""
    
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Calculate all technical indicators for a given DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary of indicator Series
        """
        indicators = {}
        
        # Moving Averages
        indicators['EMA20'] = TechnicalIndicators.ema(df['Close'], period=20)
        indicators['EMA50'] = TechnicalIndicators.ema(df['Close'], period=50)
        
        # Volume
        indicators['Volume_MA20'] = TechnicalIndicators.sma(df['Volume'], period=20)
        
        # Momentum
        indicators['RSI'] = TechnicalIndicators.rsi(df['Close'])
        
        return indicators
    
    @staticmethod
    def ema(series: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return series.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def sma(series: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Simple Moving Average."""
        return series.rolling(window=period).mean()
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_trend_strength(df: pd.DataFrame) -> float:
        """Calculate trend strength using EMA ratio."""
        return (df['EMA20'].iloc[-1] / df['EMA50'].iloc[-1] - 1) * 100
    
    @staticmethod
    def calculate_volume_ratio(df: pd.DataFrame) -> float:
        """Calculate volume strength using current vs average volume."""
        return df['Volume'].iloc[-1] / df['Volume_MA20'].iloc[-1]
    
    @staticmethod
    def calculate_momentum(df: pd.DataFrame, period: int = 20) -> float:
        """Calculate price momentum as percentage change."""
        return (df['Close'].iloc[-1] / df['Close'].iloc[-period] - 1) * 100
