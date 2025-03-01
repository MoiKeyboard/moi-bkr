import backtrader as bt

class MovingAverageStrategy(bt.Strategy):
    """
    A simple moving average crossover strategy with fixed percentage-based stop-loss and take-profit.

    This strategy enters a trade when the short moving average crosses above the long moving average.
    It exits the trade if:
    - The price drops below the stop-loss level (fixed percentage)
    - The price reaches the take-profit level (fixed percentage)
    - The short MA crosses below the long MA

    Optional kwargs:
        short_period (int): Lookback period for short moving average (default: 10)
        long_period (int): Lookback period for long moving average (default: 30)
        stop_loss_pct (float): Stop-loss percentage below entry price (default: 0.95, i.e., 5% loss)
        take_profit_pct (float): Take-profit percentage above entry price (default: 1.10, i.e., 10% profit)
    """

    def __init__(self, **kwargs):
        """
        Initialize indicators for the moving averages and track the buy price.

        Args:
            kwargs: Optional parameters for customizing the strategy.
        """
        # Retrieve optional parameters with defaults
        self.short_period = kwargs.get("short_period", 10)
        self.long_period = kwargs.get("long_period", 30)
        self.stop_loss_pct = kwargs.get("stop_loss_pct", 0.95)  # 5% stop-loss
        self.take_profit_pct = kwargs.get("take_profit_pct", 1.10)  # 10% take-profit

        # Define moving averages
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.long_period)

        # Track entry price
        self.buy_price = None

    def next(self):
        """
        Trading logic executed on each new bar.
        """
        if self.position:  # If already in a trade
            # Check if stop-loss is triggered
            if self.data.close[0] < self.buy_price * self.stop_loss_pct:
                self.close()
                print(f"Stop-loss triggered at {self.data.close[0]}")

            # Check if take-profit is triggered
            elif self.data.close[0] > self.buy_price * self.take_profit_pct:
                self.close()
                print(f"Take-profit triggered at {self.data.close[0]}")

            # Exit trade if short MA falls below long MA
            elif self.short_ma[0] < self.long_ma[0]:
                self.close()
                print(f"Moving average crossover exit at {self.data.close[0]}")
        else:
            # Enter trade if short MA crosses above long MA
            if self.short_ma[0] > self.long_ma[0]:
                self.buy()
                self.buy_price = self.data.close[0]  # Store the buy price
                print(f"Entered trade at {self.buy_price}")

class ATRMovingAverageStrategy(bt.Strategy):
    """
    A moving average crossover strategy with ATR-based dynamic stop-loss and take-profit levels.

    This strategy enters a trade when the short moving average crosses above the long moving average.
    It exits the trade if:
    - The price drops below an ATR-based stop-loss level
    - The price reaches an ATR-based take-profit level

    It also uses ATR to adjust position sizes dynamically based on market volatility.

    Optional kwargs:
        short_period (int): Lookback period for short moving average (default: 10)
        long_period (int): Lookback period for long moving average (default: 30)
        stop_loss_multiplier (float): ATR multiplier for stop-loss (default: 1.5)
        take_profit_multiplier (float): ATR multiplier for take-profit (default: 3.0)
    """

    def __init__(self, **kwargs):
        """
        Initialize the moving average crossover strategy with ATR-based risk management.

        Args:
            kwargs: Optional parameters for customizing the strategy.
        """
        # Retrieve optional parameters with defaults
        self.short_period = kwargs.get("short_period", 20)
        self.long_period = kwargs.get("long_period", 80)
        self.stop_loss_multiplier = kwargs.get("stop_loss_multiplier", 2)
        self.take_profit_multiplier = kwargs.get("take_profit_multiplier", 6)

        # Define moving averages
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.long_period)

        # Define ATR for dynamic stop-loss and take-profit
        self.atr = bt.indicators.AverageTrueRange(self.data, period=14)

        # Track entry price
        self.entry_price = None

    def next(self):
        """
        Execute trading logic on each new bar.

        - Uses ATR to determine position size dynamically.
        - Adjusts trade size based on volatility.
        """
        if not self.position:  # No open trades
            if self.short_ma[0] > self.long_ma[0]:  # Bullish crossover
                atr_value = self.atr[0]  # Get current ATR
                risk_per_trade = 0.02  # Risk 2% of capital
                capital = self.broker.get_cash()  # Get available capital
                position_size = (capital * risk_per_trade) / atr_value  # ATR-based sizing
                
                self.buy(size=position_size)
                self.entry_price = self.data.close[0]
                print(f"Entered trade at {self.entry_price} with size {position_size}")
        
        else:  # Already in a trade
            # Stop-loss and take-profit dynamically set based on ATR
            stop_loss_price = self.entry_price - (self.atr[0] * self.stop_loss_multiplier)
            take_profit_price = self.entry_price + (self.atr[0] * self.take_profit_multiplier)

            if self.data.close[0] <= stop_loss_price:
                self.close()
                print(f"Stop-loss triggered at {self.data.close[0]}")
            elif self.data.close[0] >= take_profit_price:
                self.close()
                print(f"Take-profit triggered at {self.data.close[0]}")