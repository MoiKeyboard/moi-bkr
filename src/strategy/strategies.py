import pandas as pd
import backtrader as bt
from src.strategy.indicators import VWAP, OBV
import numpy as np


class BaseStrategy:
    """
    Base mixin class for trading strategies.

    This class defines the expected interface for a trading strategy.
    """

    def generate_signals(self, market_data):
        """
        Process market data and return a trading signal.

        Args:
            market_data: Market data input (type depends on the strategy's implementation).

        Returns:
            tuple: (signal: str, processed_data)
        """
        raise NotImplementedError("Subclasses must implement generate_signals()")


class MovingAverageStrategy(bt.Strategy, BaseStrategy):
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
        """Initialize indicators for the moving averages and track the buy price."""
        self.short_period = kwargs.get("short_period", 10)
        self.long_period = kwargs.get("long_period", 30)
        self.stop_loss_pct = kwargs.get("stop_loss_pct", 0.95)  # 5% stop-loss
        self.take_profit_pct = kwargs.get("take_profit_pct", 1.10)  # 10% take-profit

        self.short_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.short_period
        )
        self.long_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.long_period
        )

        self.buy_price = None

    def next(self):
        """Trading logic executed on each new bar."""
        if self.position:
            if self.data.close[0] < self.buy_price * self.stop_loss_pct:
                self.close()
                print(f"Stop-loss triggered at {self.data.close[0]}")

            elif self.data.close[0] > self.buy_price * self.take_profit_pct:
                self.close()
                print(f"Take-profit triggered at {self.data.close[0]}")

            elif self.short_ma[0] < self.long_ma[0]:
                self.close()
                print(f"Moving average crossover exit at {self.data.close[0]}")
        else:
            if self.short_ma[0] > self.long_ma[0]:
                self.buy()
                self.buy_price = self.data.close[0]
                print(f"Entered trade at {self.buy_price}")

    def generate_signals(self, df):
        """Placeholder for non-Backtrader implementations."""
        return None, df


class ATRMovingAverageStrategy(bt.Strategy, BaseStrategy):
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
        """Initialize the moving average crossover strategy with ATR-based risk management."""
        self.short_period = kwargs.get("short_period", 20)
        self.long_period = kwargs.get("long_period", 80)
        self.stop_loss_multiplier = kwargs.get("stop_loss_multiplier", 2)
        self.take_profit_multiplier = kwargs.get("take_profit_multiplier", 6)

        self.short_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.short_period
        )
        self.long_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.long_period
        )

        self.atr = bt.indicators.AverageTrueRange(self.data, period=14)

        self.entry_price = None

    def next(self):
        """Execute trading logic on each new bar."""
        if not self.position:
            if self.short_ma[0] > self.long_ma[0]:
                atr_value = self.atr[0]
                risk_per_trade = 0.02
                capital = self.broker.get_cash()
                position_size = (capital * risk_per_trade) / atr_value

                self.buy(size=position_size)
                self.entry_price = self.data.close[0]
                print(f"Entered trade at {self.entry_price} with size {position_size}")

        else:
            stop_loss_price = self.entry_price - (
                self.atr[0] * self.stop_loss_multiplier
            )
            take_profit_price = self.entry_price + (
                self.atr[0] * self.take_profit_multiplier
            )

            if self.data.close[0] <= stop_loss_price:
                self.close()
                print(f"Stop-loss triggered at {self.data.close[0]}")
            elif self.data.close[0] >= take_profit_price:
                self.close()
                print(f"Take-profit triggered at {self.data.close[0]}")

    def generate_signals(self, df):
        """Placeholder for non-Backtrader implementations."""
        return None, df


class VWAPStrategy(BaseStrategy, bt.Strategy):
    """
    Volume-Weighted Average Price (VWAP) trading strategy.

    - Generates signals based on price relative to VWAP.
    - Works with both Backtrader (for backtesting) and DataFrames (for external execution).

    Optional kwargs:
        vwap_period (int): Number of periods for VWAP calculation (default: 20).
    """

    def __init__(self, **kwargs):
        """
        Initialize VWAP strategy.

        Args:
            kwargs: Optional parameters.
        """
        self.vwap_period = kwargs.get("vwap_period", 20)  # Default 20-period VWAP
        self.data_vwap = []  # Store VWAP calculations

    def calculate_vwap(self, df):
        """
        Compute VWAP manually using price and volume.

        Args:
            df (pd.DataFrame): Market data with 'close', 'volume' columns.

        Returns:
            pd.Series: VWAP values for the given data.
        """
        df["cum_vol_price"] = (df["close"] * df["volume"]).cumsum()
        df["cum_vol"] = df["volume"].cumsum()
        df["vwap"] = df["cum_vol_price"] / df["cum_vol"]
        return df["vwap"]

    def generate_signals(self, df):
        """
        Generate trading signals based on VWAP.

        Args:
            df (pd.DataFrame): Market data.

        Returns:
            tuple: (signal: str, df with VWAP)
        """
        if "volume" not in df.columns:
            raise ValueError(
                "Market data must include a 'volume' column for VWAP calculation."
            )

        df["VWAP"] = self.calculate_vwap(df)

        last_close = df["close"].iloc[-1]
        last_vwap = df["VWAP"].iloc[-1]

        if last_close > last_vwap * 1.005:  # 0.5% above VWAP
            return "BUY", df
        elif last_close < last_vwap * 0.995:  # 0.5% below VWAP
            return "SELL", df
        else:
            return "HOLD", df

    def next(self):
        """
        Implement VWAP trading logic for Backtrader.

        - If price is above VWAP, enter a long position.
        - If price is below VWAP, close position.
        """
        vwap = self.calculate_vwap(
            pd.DataFrame(
                {"close": self.data.close.array, "volume": self.data.volume.array}
            )
        ).iloc[-1]

        if self.data.close[0] > vwap and not self.position:
            self.buy()
            print(f"BUY signal at {self.data.close[0]}")
        elif self.data.close[0] < vwap and self.position:
            self.close()
            print(f"SELL signal at {self.data.close[0]}")


class ATRVWAPStrategy(bt.Strategy):
    """
    A combined strategy using:
    - ATR-based moving average crossover for entries/exits
    - VWAP for trend confirmation

    The strategy:
    - Enters a trade when ATR-based MA crossover occurs **AND** price is above VWAP.
    - Exits if ATR-based stop-loss/take-profit triggers **OR** price falls below VWAP.
    """

    def __init__(self, **kwargs):
        """
        Initialize both ATR-based and VWAP indicators.

        Args:
            kwargs: Optional parameters for customizing the strategy.
        """
        # ATR Moving Average Parameters
        self.short_period = kwargs.get("short_period", 20)
        self.long_period = kwargs.get("long_period", 80)
        self.stop_loss_multiplier = kwargs.get("stop_loss_multiplier", 2)
        self.take_profit_multiplier = kwargs.get("take_profit_multiplier", 6)

        # VWAP Indicator
        self.vwap = VWAP(self.data)

        # ATR & Moving Averages
        self.short_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.short_period
        )
        self.long_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.long_period
        )
        self.atr = bt.indicators.AverageTrueRange(self.data, period=14)

        self.entry_price = None

    def next(self):
        """
        Execute trading logic on each new bar.
        """
        if not self.position:  # If no open position
            if self.short_ma[0] > self.long_ma[0] and self.data.close[0] > self.vwap[0]:
                # Confirm trade with VWAP trend
                atr_value = self.atr[0]
                capital = self.broker.get_cash()
                risk_per_trade = 0.02
                position_size = (capital * risk_per_trade) / atr_value

                self.buy(size=position_size)
                self.entry_price = self.data.close[0]
                print(f"Entered trade at {self.entry_price} with size {position_size}")

        else:  # Already in a trade
            stop_loss_price = self.entry_price - (
                self.atr[0] * self.stop_loss_multiplier
            )
            take_profit_price = self.entry_price + (
                self.atr[0] * self.take_profit_multiplier
            )

            # Exit if stop-loss, take-profit, or VWAP trend reversal
            if (
                self.data.close[0] <= stop_loss_price
                or self.data.close[0] < self.vwap[0]
            ):
                self.close()
                print(f"Stop-loss/VWAP exit at {self.data.close[0]}")
            elif self.data.close[0] >= take_profit_price:
                self.close()
                print(f"Take-profit exit at {self.data.close[0]}")


class SmartTrendStrategy(bt.Strategy, BaseStrategy):
    """
    An enhanced version of ATRMovingAverageStrategy with additional filters.

    Core strategy:
    - Uses EMA crossover for primary trend identification
    - MACD for trend confirmation
    - ATR for volatility-based position sizing and stops
    - Conservative entry filters to reduce false signals

    Entry conditions (need 2 out of 3):
    - EMA crossover (primary signal)
    - MACD confirmation
    - RSI in favorable zone (>40 for longs, <60 for shorts)

    Exit conditions (any):
    - Stop-loss hit (1.5 * ATR)
    - Take-profit hit (3.0 * ATR)
    - Trend reversal (EMA crossover in opposite direction)

    Risk Management:
    - Position sizing based on ATR and fixed risk per trade
    - Trailing stop-loss for winning trades
    - Maximum position size limit

    Optional kwargs:
        fast_ema (int): Fast EMA period (default: 20)
        slow_ema (int): Slow EMA period (default: 50)
        signal_ema (int): MACD signal period (default: 9)
        rsi_period (int): RSI period (default: 14)
        atr_period (int): ATR period (default: 14)
        risk_per_trade (float): Risk per trade as % of portfolio (default: 0.01)
        atr_stop_multiplier (float): ATR multiplier for stops (default: 1.5)
        atr_target_multiplier (float): ATR multiplier for targets (default: 3.0)
    """

    def __init__(self, **kwargs):
        """Initialize indicators and strategy parameters."""
        # Strategy parameters
        self.fast_ema_period = kwargs.get("fast_ema", 20)
        self.slow_ema_period = kwargs.get("slow_ema", 50)
        self.signal_ema_period = kwargs.get("signal_ema", 9)
        self.rsi_period = kwargs.get("rsi_period", 14)
        self.atr_period = kwargs.get("atr_period", 14)
        self.risk_per_trade = kwargs.get("risk_per_trade", 0.01)  # 1% risk per trade
        self.atr_stop_multiplier = kwargs.get("atr_stop_multiplier", 1.5)
        self.atr_target_multiplier = kwargs.get("atr_target_multiplier", 3.0)

        # Trend indicators
        self.fast_ema = bt.indicators.EMA(period=self.fast_ema_period)
        self.slow_ema = bt.indicators.EMA(period=self.slow_ema_period)

        # Momentum indicators
        self.macd = bt.indicators.MACD(
            period_me1=self.fast_ema_period,
            period_me2=self.slow_ema_period,
            period_signal=self.signal_ema_period,
        )
        self.rsi = bt.indicators.RSI(period=self.rsi_period)

        # Volatility indicator
        self.atr = bt.indicators.ATR(period=self.atr_period)

        # Track our position and orders
        self.order = None
        self.stop_order = None
        self.target_order = None
        self.entry_price = None
        self.position_size = None
        self.trailing_stop = None

    def calculate_position_size(self, stop_distance):
        """Calculate position size based on risk management rules."""
        if stop_distance == 0:
            return 0

        portfolio_value = self.broker.getvalue()
        risk_amount = portfolio_value * self.risk_per_trade
        position_size = risk_amount / stop_distance

        # Limit position size to 5% of portfolio value
        max_position_value = portfolio_value * 0.05
        max_position_size = max_position_value / self.data.close[0]

        return int(min(position_size, max_position_size))

    def should_long(self):
        """Check if conditions are met for a long entry."""
        # Primary trend
        trend_up = self.fast_ema[0] > self.slow_ema[0]

        # Confirmations (need 2 out of 3)
        confirmations = 0

        # 1. Trend strength
        if self.fast_ema[0] > self.fast_ema[-1]:
            confirmations += 1

        # 2. MACD confirmation
        if self.macd.macd[0] > self.macd.signal[0]:
            confirmations += 1

        # 3. RSI not overbought and in uptrend zone
        if 40 < self.rsi[0] < 70:
            confirmations += 1

        return trend_up and confirmations >= 2

    def should_short(self):
        """Check if conditions are met for a short entry."""
        # Primary trend
        trend_down = self.fast_ema[0] < self.slow_ema[0]

        # Confirmations (need 2 out of 3)
        confirmations = 0

        # 1. Trend strength
        if self.fast_ema[0] < self.fast_ema[-1]:
            confirmations += 1

        # 2. MACD confirmation
        if self.macd.macd[0] < self.macd.signal[0]:
            confirmations += 1

        # 3. RSI not oversold and in downtrend zone
        if 30 < self.rsi[0] < 60:
            confirmations += 1

        return trend_down and confirmations >= 2

    def next(self):
        """Execute trading logic on each bar."""
        if self.order:
            return

        if self.position:
            # Update trailing stop if in profit
            if self.position.size > 0:  # Long position
                if self.data.close[0] > self.entry_price:
                    new_stop = (
                        self.data.close[0] - self.atr[0] * self.atr_stop_multiplier
                    )
                    if new_stop > self.trailing_stop:
                        self.trailing_stop = new_stop

                if self.data.close[0] < self.trailing_stop:
                    self.close()
                    print(f"Trailing stop hit at {self.data.close[0]}")

            else:  # Short position
                if self.data.close[0] < self.entry_price:
                    new_stop = (
                        self.data.close[0] + self.atr[0] * self.atr_stop_multiplier
                    )
                    if new_stop < self.trailing_stop:
                        self.trailing_stop = new_stop

                if self.data.close[0] > self.trailing_stop:
                    self.close()
                    print(f"Trailing stop hit at {self.data.close[0]}")
            return

        atr_value = self.atr[0]

        if self.should_long():
            stop_price = self.data.close[0] - atr_value * self.atr_stop_multiplier
            target_price = self.data.close[0] + atr_value * self.atr_target_multiplier

            self.position_size = self.calculate_position_size(
                self.data.close[0] - stop_price
            )

            if self.position_size > 0:
                self.order = self.buy(size=self.position_size)
                self.entry_price = self.data.close[0]
                self.trailing_stop = stop_price
                print(
                    f"LONG Entry at {self.entry_price:.2f}, Size: {self.position_size}, Stop: {stop_price:.2f}"
                )

        elif self.should_short():
            stop_price = self.data.close[0] + atr_value * self.atr_stop_multiplier
            target_price = self.data.close[0] - atr_value * self.atr_target_multiplier

            self.position_size = self.calculate_position_size(
                stop_price - self.data.close[0]
            )

            if self.position_size > 0:
                self.order = self.sell(size=self.position_size)
                self.entry_price = self.data.close[0]
                self.trailing_stop = stop_price
                print(
                    f"SHORT Entry at {self.entry_price:.2f}, Size: {self.position_size}, Stop: {stop_price:.2f}"
                )

    def notify_order(self, order):
        """Handle order status updates."""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, {order.executed.price:.2f}")
            elif order.issell():
                self.log(f"SELL EXECUTED, {order.executed.price:.2f}")

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def log(self, txt, dt=None):
        """Logging function."""
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()} {txt}")
