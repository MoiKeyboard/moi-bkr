from tws.trading_bot import TradingBot
from strategy.strategies import ATRMovingAverageStrategy, MovingAverageStrategy

bot = TradingBot(
    symbol="AAPL",
    strategy_class=MovingAverageStrategy,  # or ATRMovingAverageStrategy
    strategy_kwargs={"short_period": 10, "long_period": 30},
    quantity=10,
    paper_trading=True
)

bot.run_forever()