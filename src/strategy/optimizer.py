import os
import backtrader as bt
from strategy.strategies import ATRMovingAverageStrategy


class MovingAverageOptimizer:
    """
    A class to optimize the ATR-based moving average crossover strategy.

    Args:
        data_file (str): Path to the historical data CSV file.
    """

    def __init__(self, data_file):
        self.data_file = data_file

    def run_backtest(
        self,
        short_period,
        long_period,
        stop_loss_multiplier=2,
        take_profit_multiplier=6,
    ):
        """
        Runs a backtest with the given moving average periods and risk settings.

        Args:
            short_period (int): Period for the short moving average.
            long_period (int): Period for the long moving average.
            stop_loss_multiplier (float): ATR-based stop-loss multiplier.
            take_profit_multiplier (float): ATR-based take-profit multiplier.

        Returns:
            dict: Performance metrics including Sharpe ratio.
        """
        cerebro = bt.Cerebro()
        cerebro.addstrategy(
            ATRMovingAverageStrategy,
            short_period=short_period,
            long_period=long_period,
            stop_loss_multiplier=stop_loss_multiplier,
            take_profit_multiplier=take_profit_multiplier,
        )

        data = bt.feeds.GenericCSVData(
            dataname=self.data_file,
            dtformat="%Y-%m-%d",
            timeframe=bt.TimeFrame.Days,
            compression=1,
            openinterest=-1,
            headers=True,
        )

        cerebro.adddata(data)
        cerebro.broker.set_cash(10000)  # Starting capital

        # ✅ Add Sharpe Ratio analyzer
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=0.0)

        results = cerebro.run()
        strategy = results[0]

        # ✅ Retrieve Sharpe Ratio correctly
        sharpe_ratio = strategy.analyzers.sharpe.get_analysis().get("sharperatio", 0)

        return {
            "short_period": short_period,
            "long_period": long_period,
            "sharpe_ratio": sharpe_ratio,
        }

    def optimize_ma_periods(self, short_ma_list, long_ma_list):
        """
        Optimizes the moving average periods to maximize the Sharpe ratio.

        Args:
            short_ma_list (list): List of short MA periods to test.
            long_ma_list (list): List of long MA periods to test.

        Returns:
            tuple: Best (short_period, long_period) based on Sharpe ratio.
        """
        best_config = None
        best_sharpe = float("-inf")

        for short_period in short_ma_list:
            for long_period in long_ma_list:
                if short_period >= long_period:
                    continue  # Skip invalid configurations

                result = self.run_backtest(short_period, long_period)
                if result["sharpe_ratio"] > best_sharpe:
                    best_sharpe = result["sharpe_ratio"]
                    best_config = (result["short_period"], result["long_period"])

        return best_config
