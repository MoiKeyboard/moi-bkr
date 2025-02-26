import backtrader as bt

class MovingAverageStrategy(bt.Strategy):
    params = (
        ("short_period", 10),
        ("long_period", 30),
    )

    def __init__(self):
        self.short_ma = bt.indicators.SimpleMovingAverage(period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(period=self.params.long_period)

    def next(self):
        # Check if already in a trade
        if self.position:
            # If in a trade, exit when short MA falls below long MA
            if self.short_ma < self.long_ma:
                self.close()
        else:
            # If not in a trade, enter when short MA crosses above long MA
            if self.short_ma > self.long_ma:
                self.buy()
