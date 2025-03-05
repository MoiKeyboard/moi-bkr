import backtrader as bt
import numpy as np


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
    
    lines = ('obv',)  # Define the line names
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
