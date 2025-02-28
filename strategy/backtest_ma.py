import os
from strategy.optimizer import MovingAverageOptimizer

script_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(script_dir, "historical_prices.csv")

optimizer = MovingAverageOptimizer(data_file)

# Define MA period ranges
short_ma_list = [10, 20, 30, 40, 50]
long_ma_list = [60, 80, 100, 120, 150]

# Run optimization
best_ma_config = optimizer.optimize_ma_periods(short_ma_list, long_ma_list)

print(f"Best MA config: Short={best_ma_config[0]}, Long={best_ma_config[1]}")
