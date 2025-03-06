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


class EnhancedATRStrategy(bt.Strategy, BaseStrategy):
    """
    An enhanced version of ATRMovingAverageStrategy with additional filters.

    Core strategy:
    - Uses EMA crossover for primary trend identification
    - MACD for trend confirmation
    - ATR for volatility-based position sizing and stops

    Entry conditions (need 2 out of 3):
    - EMA crossover (primary signal)
    - MACD confirmation
    - RSI in favorable zone (>40 for longs, <60 for shorts)

    Exit conditions (any):
    - Trailing stop-loss hit (1.5 * ATR)
    - Take-profit hit (2.0 * ATR)
    - Trend reversal with confirmation

    Risk Management:
    - Position sizing based on ATR and fixed risk per trade
    - Trailing stop-loss for winning trades
    - Maximum position size limit
    """

    def __init__(self, **kwargs):
        """Initialize indicators and strategy parameters."""
        # Strategy parameters
        self.fast_ema_period = kwargs.get("fast_ema", 5)  # Even faster EMA
        self.slow_ema_period = kwargs.get("slow_ema", 15)  # Shorter slow EMA
        self.signal_ema_period = kwargs.get("signal_ema", 9)
        self.rsi_period = kwargs.get("rsi_period", 14)
        self.atr_period = kwargs.get("atr_period", 14)
        self.risk_per_trade = kwargs.get("risk_per_trade", 0.01)
        self.atr_stop_multiplier = kwargs.get("atr_stop_multiplier", 1.5)
        self.atr_target_multiplier = kwargs.get("atr_target_multiplier", 2.0)
        self.max_holding_days = kwargs.get("max_holding_days", 15)

        # Initialize indicators
        self.fast_ema = bt.indicators.EMA(period=self.fast_ema_period)
        self.slow_ema = bt.indicators.EMA(period=self.slow_ema_period)
        self.macd = bt.indicators.MACD(
            period_me1=self.fast_ema_period,
            period_me2=self.slow_ema_period,
            period_signal=self.signal_ema_period,
        )
        self.rsi = bt.indicators.RSI(period=self.rsi_period)
        self.atr = bt.indicators.ATR(period=self.atr_period)

        # Track position info
        self.order = None
        self.entry_price = None
        self.position_size = None
        self.trailing_stop = None
        self.entry_bar = 0
        self.consecutive_losses = 0

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
        """Simplified long entry conditions."""
        # Basic trend check
        trend_up = self.fast_ema[0] > self.slow_ema[0]

        # Count confirmations
        confirmations = 0

        # 1. Price momentum
        if self.data.close[0] > self.data.close[-1]:
            confirmations += 1

        # 2. MACD
        if self.macd.macd[0] > self.macd.signal[0]:
            confirmations += 1

        # 3. RSI
        if 30 < self.rsi[0] < 70:  # Wider RSI range
            confirmations += 1

        # Need trend and at least one confirmation
        return trend_up and confirmations >= 1

    def should_short(self):
        """Simplified short entry conditions."""
        # Basic trend check
        trend_down = self.fast_ema[0] < self.slow_ema[0]

        # Count confirmations
        confirmations = 0

        # 1. Price momentum
        if self.data.close[0] < self.data.close[-1]:
            confirmations += 1

        # 2. MACD
        if self.macd.macd[0] < self.macd.signal[0]:
            confirmations += 1

        # 3. RSI
        if 30 < self.rsi[0] < 70:  # Wider RSI range
            confirmations += 1

        # Need trend and at least one confirmation
        return trend_down and confirmations >= 1

    def next(self):
        """Execute trading logic on each bar."""
        if self.order:
            return

        # Print indicator values for debugging
        if len(self) % 5 == 0:  # Print every 5 bars
            print(f"\nBar {len(self)} - Close: {self.data.close[0]:.2f}")
            print(f"EMAs - Fast: {self.fast_ema[0]:.2f}, Slow: {self.slow_ema[0]:.2f}")
            print(f"MACD: {self.macd.macd[0]:.2f}, Signal: {self.macd.signal[0]:.2f}")
            print(f"RSI: {self.rsi[0]:.2f}")

        # Check time-based exit for existing positions
        if self.position:
            bars_held = len(self) - self.entry_bar
            if bars_held > self.max_holding_days:
                self.close()
                print(f"Time-based exit at {self.data.close[0]:.2f}")
                return

            # Update trailing stop if in profit
            if self.position.size > 0:  # Long position
                if self.data.close[0] > self.entry_price:
                    new_stop = max(
                        self.data.close[0] - self.atr[0] * self.atr_stop_multiplier,
                        self.trailing_stop,
                    )
                    self.trailing_stop = new_stop

                if self.data.close[0] < self.trailing_stop:
                    self.close()
                    print(f"Long trailing stop hit at {self.data.close[0]:.2f}")

            else:  # Short position
                if self.data.close[0] < self.entry_price:
                    new_stop = min(
                        self.data.close[0] + self.atr[0] * self.atr_stop_multiplier,
                        self.trailing_stop,
                    )
                    self.trailing_stop = new_stop

                if self.data.close[0] > self.trailing_stop:
                    self.close()
                    print(f"Short trailing stop hit at {self.data.close[0]:.2f}")
            return

        # Entry logic
        if self.should_long():
            stop_price = self.data.close[0] - self.atr[0] * self.atr_stop_multiplier
            self.position_size = self.calculate_position_size(
                self.data.close[0] - stop_price
            )

            if self.position_size > 0:
                self.order = self.buy(size=self.position_size)
                self.entry_price = self.data.close[0]
                self.trailing_stop = stop_price
                self.entry_bar = len(self)
                print(
                    f"LONG Entry at {self.entry_price:.2f}, Size: {self.position_size}"
                )

        elif self.should_short():
            stop_price = self.data.close[0] + self.atr[0] * self.atr_stop_multiplier
            self.position_size = self.calculate_position_size(
                stop_price - self.data.close[0]
            )

            if self.position_size > 0:
                self.order = self.sell(size=self.position_size)
                self.entry_price = self.data.close[0]
                self.trailing_stop = stop_price
                self.entry_bar = len(self)
                print(
                    f"SHORT Entry at {self.entry_price:.2f}, Size: {self.position_size}"
                )

    def notify_trade(self, trade):
        """Track consecutive losses."""
        if trade.status == trade.Closed:
            if trade.pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
