import backtrader as bt

class MovingAverageStrategy(bt.Strategy):
    params = (
        ("short_period", 10),
        ("long_period", 30),
        ("stop_loss_pct", 0.95),  # 5% stop-loss
        ("take_profit_pct", 1.10),  # 10% take-profit
    )

    def __init__(self):
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_period)
        self.buy_price = None  # Track the price at which the position was opened

    def next(self):
        # Check if already in a trade
        if self.position:
            # Stop-loss and take-profit logic
            if self.data.close[0] < self.buy_price * self.params.stop_loss_pct:
                self.close()  # Stop-loss triggered
                print(f"Stop-loss triggered at {self.data.close[0]}")
            elif self.data.close[0] > self.buy_price * self.params.take_profit_pct:
                self.close()  # Take-profit triggered
                print(f"Take-profit triggered at {self.data.close[0]}")
            # Exit when short MA falls below long MA
            elif self.short_ma[0] < self.long_ma[0]:
                self.close()
                print(f"Moving average crossover exit at {self.data.close[0]}")
        else:
            # If not in a trade, enter when short MA crosses above long MA
            if self.short_ma[0] > self.long_ma[0]:
                self.buy()
                self.buy_price = self.data.close[0]  # Record the buy price
                print(f"Entered trade at {self.buy_price}")