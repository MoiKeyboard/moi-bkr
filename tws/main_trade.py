import time
import pandas as pd
from ib_insync import *
from strategy.strategies import ATRMovingAverageStrategy
from tws.tws_client import TWSClient

class TradingBot:
    def __init__(self, symbol, short_period=10, long_period=50, quantity=10, paper_trading=True):
        """Initializes the bot with stock symbol, strategy, and trading parameters."""
        self.symbol = symbol
        self.quantity = quantity
        self.strategy = MovingAverageStrategy(short_period, long_period)
        self.tws = TWSClient(port=7497 if paper_trading else 7496)  # Use paper/live trading
        self.tws.connect()
        self.tws.get_account()
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
        """Runs the trading bot continuously."""
        try:
            while True:
                self.trade()
                time.sleep(interval)  # Wait before checking again
        except KeyboardInterrupt:
            print("Stopping trading bot...")
            self.tws.disconnect()

# Run the bot for AAPL stock
if __name__ == "__main__":
    bot = TradingBot("AAPL", short_period=10, long_period=50, quantity=10, paper_trading=True)
    bot.run()
