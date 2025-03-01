import time
import asyncio
import backtrader as bt
from ib_insync import *
from tws.tws_client import TWSClient
import pandas as pd

class TradingBot:
    """
    A trading bot that fetches market data from IBKR and applies a chosen strategy to generate buy/sell signals.

    Args:
        symbol (str): The stock symbol to trade.
        strategy_class (BaseStrategy): The trading strategy class to use.
        strategy_kwargs (dict, optional): Parameters to initialize the strategy.
        quantity (int): Number of shares to trade per order.
        paper_trading (bool): Whether to use paper trading mode (default: True).
    """

    def __init__(self, symbol, strategy_class, strategy_kwargs=None, quantity=10, paper_trading=True):
        """Initializes the bot with stock symbol, strategy, and trading parameters."""
        self.symbol = symbol
        self.quantity = quantity
        self.strategy_kwargs = strategy_kwargs or {}

        # Detect if strategy is a Backtrader strategy
        if issubclass(strategy_class, bt.Strategy):
            self.is_backtrader = True
            self.cerebro = bt.Cerebro()
            self.cerebro.addstrategy(strategy_class, **self.strategy_kwargs)
        else:
            self.is_backtrader = False
            self.strategy = strategy_class(**self.strategy_kwargs)

        # Connect to TWS API
        self.tws = TWSClient(port=7497 if paper_trading else 7496)
        self.tws.connect()
        self.tws.get_account()

        # Define contract
        self.contract = Stock(self.symbol, 'SMART', 'USD')
        self.tws.ib.qualifyContracts(self.contract)

    def get_live_data(self):
        """Fetches latest market data from TWS."""
        bars = self.tws.ib.reqHistoricalData(
            self.contract,
            endDateTime='',
            durationStr='1 D',
            barSizeSetting='5 mins',
            whatToShow='MIDPOINT',
            useRTH=True,
            formatDate=1
        )
        if bars:
            df = util.df(bars)
            df['Date'] = pd.to_datetime(df['date'])
            return df[['Date', 'close']]
        return None

    def trade(self):
        """Executes trading strategy based on signals."""
        df = self.get_live_data()
        if df is None or df.empty:
            print("No data available, skipping trade cycle.")
            return

        if self.is_backtrader:
            print("Running Backtrader strategy in Cerebro...")
            self.cerebro.run()
            return  # Backtrader runs separately, no need for manual trade execution

        # Non-Backtrader strategies
        signal, df = self.strategy.generate_signals(df)

        if signal:
            positions = self.tws.get_positions()
            holding = any(pos["symbol"] == self.symbol and pos["quantity"] > 0 for pos in positions)

            if signal == "BUY" and not holding:
                print(f"BUY signal detected for {self.symbol}! Placing order...")
                order = MarketOrder('BUY', self.quantity)
                self.tws.ib.placeOrder(self.contract, order)

            elif signal == "SELL" and holding:
                print(f"SELL signal detected for {self.symbol}! Closing position...")
                order = MarketOrder('SELL', self.quantity)
                self.tws.ib.placeOrder(self.contract, order)

    def run(self, interval=300):
        """
        Runs the trading bot continuously at the specified interval (in seconds).
        
        This keeps the bot running and ensures the IB event loop stays active.
        """
        print("Starting trading bot...")
        try:
            while True:
                self.trade()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("Stopping trading bot...")
            self.tws.disconnect()

    def run_forever(self):
        """
        Runs the bot with Backtrader or live trading while keeping the IBKR event loop alive.

        This ensures that the bot does not exit immediately after executing a strategy.
        """
        print("Running Backtrader strategy in Cerebro...")
        self.cerebro.run()

        print("Entering IB event loop...")
        try:
            loop = asyncio.get_event_loop()
            loop.run_forever()  # Keeps the script alive
        except KeyboardInterrupt:
            print("Stopping trading bot...")
            self.tws.ib.disconnect()
