import yaml
from typing import Dict
import pandas as pd
from .data_providers.yahoo_provider import YahooFinanceProvider
from .data_providers.ib_provider import IBDataProvider
import os


class MarketScanner:
    """Scanner to identify trending stocks using configured data provider."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize scanner with configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        # Load configuration
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        self.market_config = config.get("market_analysis", {})
        self.tws_config = config.get("tws", {})

        # Initialize data provider based on configuration
        self.provider = self._create_provider()
        self.lookback = self.market_config.get("lookback_days", 100)
        self.tickers = self.market_config.get("tickers", [])

    def _create_provider(self):
        """Create the appropriate data provider based on configuration."""
        provider_type = self.market_config.get("provider", "yahoo")

        if provider_type == "yahoo":
            return YahooFinanceProvider()
        elif provider_type == "ib":
            return IBDataProvider(
                host=self.tws_config["host"],
                port=self.tws_config["port"],
                client_id=self.tws_config["client_id"],
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")

    def scan_market(self) -> pd.DataFrame:
        """
        Scan market for trending stocks.

        Returns:
            DataFrame with analysis results
        """
        # Fetch market data using provider
        market_data = self.provider.fetch_data(self.tickers, self.lookback)

        # Analyze each ticker
        results = []
        for ticker, df in market_data.items():
            try:
                metrics = self._analyze_ticker(df)
                metrics["symbol"] = ticker
                results.append(metrics)
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")

        # Create results DataFrame
        results_df = pd.DataFrame(results)

        # Sort by trend strength
        if not results_df.empty:
            results_df = results_df.sort_values("trend_strength", ascending=False)

        return results_df

    def _analyze_ticker(self, df: pd.DataFrame) -> Dict:
        """Calculate technical indicators and metrics for a ticker."""
        if df.empty:
            return {}

        # Calculate indicators
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        df["Volume_MA20"] = df["Volume"].rolling(window=20).mean()

        # Get latest values
        current_close = df["Close"].iloc[-1]
        current_volume = df["Volume"].iloc[-1]

        # Calculate metrics
        metrics = {
            "trend_strength": (df["EMA20"].iloc[-1] / df["EMA50"].iloc[-1] - 1) * 100,
            "volume_ratio": current_volume / df["Volume_MA20"].iloc[-1],
            "price_momentum": (current_close / df["Close"].iloc[-20] - 1) * 100,
            "above_ema20": current_close > df["EMA20"].iloc[-1],
            "above_ema50": current_close > df["EMA50"].iloc[-1],
            "current_price": current_close,
        }

        return metrics

    def save_market_data(self, output_dir: str = "data") -> None:
        """
        Save market data for all tickers to CSV files.

        Args:
            output_dir: Directory to save CSV files (will be created if doesn't exist)
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Fetch market data
        market_data = self.provider.fetch_data(self.tickers, self.lookback)

        # Save each ticker's data
        for ticker, df in market_data.items():
            try:
                filename = os.path.join(output_dir, f"{ticker}_historical.csv")
                df.to_csv(filename)
                print(f"Saved {ticker} data to {filename}")
            except Exception as e:
                print(f"Error saving {ticker} data: {e}")


def main():
    """Example usage of MarketScanner."""
    scanner = MarketScanner()
    results = scanner.scan_market()

    pd.set_option("display.max_columns", None)
    print("\nMarket Scanner Results:")
    print("=====================")
    print(results)

    print("\nStrong Trending Stocks:")
    print("=====================")
    strong_trends = results[
        (results["trend_strength"] > 0)
        & (results["volume_ratio"] > 1)
        & (results["above_ema20"])
    ]

    columns_to_show = [
        "symbol",
        "trend_strength",
        "volume_ratio",
        "price_momentum",
        "current_price",
    ]
    print(strong_trends[columns_to_show])


if __name__ == "__main__":
    main()
    scanner.save_market_data(output_dir="strategy/historical_data")
