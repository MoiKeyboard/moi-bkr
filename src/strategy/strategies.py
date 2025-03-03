import pandas as pd
import backtrader as bt
from strategy.indicators import VWAP  

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

        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.long_period)

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

        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.long_period)

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
            stop_loss_price = self.entry_price - (self.atr[0] * self.stop_loss_multiplier)
            take_profit_price = self.entry_price + (self.atr[0] * self.take_profit_multiplier)

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
            raise ValueError("Market data must include a 'volume' column for VWAP calculation.")

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
        vwap = self.calculate_vwap(pd.DataFrame({
            "close": self.data.close.array,
            "volume": self.data.volume.array
        })).iloc[-1]

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
        self.short_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.short_period)
        self.long_ma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.long_period)
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
            stop_loss_price = self.entry_price - (self.atr[0] * self.stop_loss_multiplier)
            take_profit_price = self.entry_price + (self.atr[0] * self.take_profit_multiplier)

            # Exit if stop-loss, take-profit, or VWAP trend reversal
            if self.data.close[0] <= stop_loss_price or self.data.close[0] < self.vwap[0]:
                self.close()
                print(f"Stop-loss/VWAP exit at {self.data.close[0]}")
            elif self.data.close[0] >= take_profit_price:
                self.close()
                print(f"Take-profit exit at {self.data.close[0]}")