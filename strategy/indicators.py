import backtrader as bt

class VWAP(bt.Indicator):
    """
    Custom Volume-Weighted Average Price (VWAP) Indicator.
    
    VWAP is calculated as:
        VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)

    It is used to determine market trends and fair value.
    """
    alias = ('VWAP',)
    lines = ('vwap',)
    params = dict(period=14)  # Default period

    def __init__(self):
        """Initialize VWAP calculation components."""
        typical_price = (self.data.high + self.data.low + self.data.close) / 3
        volume = self.data.volume

        self.cum_tp_vol = bt.indicators.SumN(typical_price * volume, period=self.p.period)
        self.cum_vol = bt.indicators.SumN(volume, period=self.p.period)
        self.lines.vwap = self.cum_tp_vol / self.cum_vol
