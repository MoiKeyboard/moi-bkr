import yaml
from typing import Dict, List
import pandas as pd
from .data_providers.yahoo_provider import YahooFinanceProvider
from .data_providers.ib_provider import IBDataProvider
import os
import logging
from src.strategy.indicators import TechnicalIndicators
from pathlib import Path


class MarketScanner:
    """Scanner to identify trending stocks using configured data provider."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize scanner with configuration.
        Environment is controlled by ENV_MODE environment variable.
        """
        self.config_path = config_path
        self.logger = logging.getLogger(self.__class__.__name__)

        # Determine environment from environment variable
        self.env = os.getenv("ENV_MODE", "dev")
        self.logger.info(f"Running in {self.env} environment")

        # Load configuration
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        self.market_config = config.get("market_analysis", {})
        self.tws_config = config.get("tws", {})

        # Get environment-specific data directory
        self.data_dir = self._get_data_directory()
        self.logger.info(f"Using data directory: {self.data_dir}")

        # Initialize data provider and settings
        self.provider = self._create_provider()
        self.lookback = self.market_config.get("lookback_days", 100)
        self.tickers = self.market_config.get("tickers", [])

    def add_tickers(self, tickers: List[str]) -> None:
        """
        Add tickers to watchlist, handling edge cases.
        
        Args:
            tickers: List of ticker symbols to add
        """
        if not tickers:
            self.logger.warning("No tickers provided to add")
            return
        
        # Convert to uppercase and remove duplicates
        new_tickers = [t.upper() for t in tickers if isinstance(t, str)]
        new_tickers = list(set(new_tickers))
        
        # Filter out already existing tickers
        existing_tickers = set(self.tickers)
        actually_new = [t for t in new_tickers if t not in existing_tickers]
        
        if not actually_new:
            self.logger.info("No new tickers to add (all already exist)")
            return
        
        # Add new tickers
        self.tickers.extend(actually_new)
        self.logger.info(f"Added {len(actually_new)} new tickers: {actually_new}")
        
        # Update config
        self._update_config()

    def remove_tickers(self, tickers: List[str]) -> None:
        """
        Remove tickers from watchlist, handling edge cases.
        
        Args:
            tickers: List of ticker symbols to remove
        """
        if not tickers:
            self.logger.warning("No tickers provided to remove")
            return
        
        # Convert to uppercase for comparison
        remove_set = set(t.upper() for t in tickers if isinstance(t, str))
        
        # Find tickers that actually exist
        existing_set = set(self.tickers)
        to_remove = remove_set.intersection(existing_set)
        
        if not to_remove:
            self.logger.info("No matching tickers found to remove")
            return
        
        # Remove tickers
        self.tickers = [t for t in self.tickers if t not in to_remove]
        self.logger.info(f"Removed {len(to_remove)} tickers: {to_remove}")
        
        # Update config
        self._update_config()

    def get_tickers(self) -> List[str]:
        """
        Get current watchlist tickers.
        
        Returns:
            List of ticker symbols
        """
        return self.tickers.copy()  # Return copy to prevent external modification

    def _update_config(self) -> None:
        """Update the config file with current tickers."""
        try:
            # Read current config
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            # Update tickers
            config["market_analysis"]["tickers"] = self.tickers

            # Write updated config
            with open(self.config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False)

        except Exception as e:
            self.logger.error(f"Failed to update config file: {e}")
            raise

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

    def _get_data_filename(self, ticker: str, latest_date: str) -> str:
        """Generate filename for ticker data."""
        return os.path.join(self.data_dir, f"{ticker}_{latest_date}.csv")

    def _get_analysis_filename(self) -> str:
        """Generate filename for analysis results with current date."""
        current_date = pd.Timestamp.now()

        # If weekend, use Friday's date
        if current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            days_to_subtract = current_date.weekday() - 4  # 4 = Friday
            current_date = current_date - pd.Timedelta(days=days_to_subtract)

        date_str = current_date.strftime("%Y%m%d")
        return os.path.join(self.data_dir, f"market_analysis_results_{date_str}.csv")

    def scan_market(self) -> None:
        """
        Scan market and update data files for all tickers.
        Only fetches new data if needed.
        """
        self.logger.info("Starting market scan...")

        # Get current date and check if it's a weekend
        current_date = pd.Timestamp.now()
        is_weekend = current_date.weekday() >= 5  # 5 = Saturday, 6 = Sunday

        # If it's weekend, use last Friday's date
        if is_weekend:
            days_to_subtract = current_date.weekday() - 4  # 4 = Friday
            current_date = current_date - pd.Timedelta(days=days_to_subtract)

        current_date_str = current_date.strftime("%Y%m%d")

        for ticker in self.tickers:
            try:
                # Check if we need to update data
                existing_file = None
                for file in os.listdir(self.data_dir):
                    if file.startswith(f"{ticker}_"):
                        existing_file = os.path.join(self.data_dir, file)
                        break

                if existing_file:
                    # Read existing data to check latest date
                    df = pd.read_csv(existing_file, index_col=0, parse_dates=True)
                    latest_date = df.index[-1].strftime("%Y%m%d")

                    # Skip if data is current (using the adjusted current date)
                    if latest_date >= current_date_str:
                        self.logger.info(
                            f"{ticker}: Data is current (last: {latest_date}, current: {current_date_str}), skipping..."
                        )
                        continue

                # Fetch new data only if needed
                self.logger.info(f"Fetching data for {ticker}...")
                market_data = self.provider.fetch_data([ticker], self.lookback)

                if ticker in market_data:
                    df = market_data[ticker]
                    latest_date = df.index[-1].strftime("%Y%m%d")

                    # Save to new file
                    new_filename = self._get_data_filename(ticker, latest_date)
                    df.to_csv(new_filename)

                    # Remove old file if it exists
                    if existing_file and existing_file != new_filename:
                        os.remove(existing_file)

                    self.logger.info(f"Updated data for {ticker}")

            except Exception as e:
                self.logger.error(f"Error updating {ticker}: {e}")

    def analyze_tickers(self, force_update: bool = False) -> pd.DataFrame:
        """
        Analyze all tickers and generate results.
        Only updates analysis if data has changed or force_update is True.

        Args:
            force_update: Force reanalysis even if no data changes

        Returns:
            DataFrame with analysis results
        """
        analysis_file = self._get_analysis_filename()

        # Remove old analysis files
        for file in os.listdir(self.data_dir):
            if file.startswith("market_analysis_results_") and file != os.path.basename(
                analysis_file
            ):
                old_file = os.path.join(self.data_dir, file)
                try:
                    os.remove(old_file)
                    self.logger.info(f"Removed old analysis file: {file}")
                except Exception as e:
                    self.logger.error(f"Error removing old analysis file {file}: {e}")

        # Check if we need to update analysis
        if not force_update and os.path.exists(analysis_file):
            # Check if any data files are newer than analysis
            analysis_mtime = os.path.getmtime(analysis_file)
            data_changed = False

            for file in os.listdir(self.data_dir):
                if file.endswith(".csv") and file != "market_analysis_results.csv":
                    if (
                        os.path.getmtime(os.path.join(self.data_dir, file))
                        > analysis_mtime
                    ):
                        data_changed = True
                        break

            if not data_changed:
                self.logger.info("Analysis is current, loading existing results...")
                return pd.read_csv(analysis_file)

        self.logger.info("Analyzing tickers...")
        results = []

        # Analyze each ticker's data
        for ticker in self.tickers:
            try:
                # Find ticker's data file
                data_file = None
                for file in os.listdir(self.data_dir):
                    if file.startswith(f"{ticker}_"):
                        data_file = os.path.join(self.data_dir, file)
                        break

                if data_file:
                    df = pd.read_csv(data_file, index_col=0, parse_dates=True)
                    metrics = self._analyze_ticker(df, ticker)
                    results.append(metrics)

            except Exception as e:
                self.logger.error(f"Error analyzing {ticker}: {e}")

        # Create and save results
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values("trend_strength", ascending=False)
            results_df.to_csv(analysis_file, index=False)
            self.logger.info("Analysis complete and saved")

        return results_df

    def _analyze_ticker(self, df: pd.DataFrame, ticker: str) -> Dict:
        """
        Calculate technical indicators and metrics for a ticker.

        Args:
            df: DataFrame containing ticker data
            ticker: Ticker symbol
        """
        if df.empty:
            return {}

        # Calculate all technical indicators
        indicators = TechnicalIndicators.calculate_all(df)
        for name, series in indicators.items():
            df[name] = series

        # Get latest values
        current_close = df["Close"].iloc[-1]

        # Calculate metrics
        metrics = {
            "symbol": ticker,
            "trend_strength": TechnicalIndicators.calculate_trend_strength(df),
            "volume_ratio": TechnicalIndicators.calculate_volume_ratio(df),
            "price_momentum": TechnicalIndicators.calculate_momentum(df),
            "rsi": df["RSI"].iloc[-1],
            "above_ema20": current_close > df["EMA20"].iloc[-1],
            "above_ema50": current_close > df["EMA50"].iloc[-1],
            "current_price": current_close,
        }

        return metrics

    def _get_data_directory(self) -> str:
        """
        Get the appropriate data directory based on environment.
        Returns absolute path to the market scanner data directory.
        """
        # Default paths for each environment
        DEFAULT_PATHS = {"dev": ".data", "prod": "/opt/trading_bot/data"}

        # Get base directory from config or use default
        config_dir = self.market_config.get("data_dir")

        # Determine base directory
        if isinstance(config_dir, dict):
            # If config specifies paths per environment
            base_dir = config_dir.get(self.env, DEFAULT_PATHS[self.env])
        elif isinstance(config_dir, str):
            # If config provides a single path, use it for prod, default for dev
            base_dir = config_dir if self.env == "prod" else DEFAULT_PATHS["dev"]
        else:
            # Use defaults if no config provided
            base_dir = DEFAULT_PATHS[self.env]

        # Create and return full path
        full_path = os.path.join(base_dir, "market_scanner")
        os.makedirs(full_path, exist_ok=True)

        self.logger.debug(f"Using data directory: {full_path}")
        return full_path

    def get_latest_analysis(self) -> Dict:
        """
        Get the most recent market analysis results.
        Returns a dictionary with analysis results and metadata.
        """
        try:
            analysis_file = self._get_analysis_filename()
            if not os.path.exists(analysis_file):
                self.logger.warning("No analysis file found")
                return {
                    "status": "error",
                    "message": "No analysis available",
                    "data": None,
                    "timestamp": None,
                }

            df = pd.read_csv(analysis_file)

            # Get strong trends
            strong_trends = df[
                (df["trend_strength"] > 0)
                & (df["volume_ratio"] > 1)
                & (df["above_ema20"])
            ]

            # Format the results
            return {
                "status": "success",
                "message": "Analysis retrieved successfully",
                "data": {
                    "all_stocks": df.to_dict(orient="records"),
                    "strong_trends": strong_trends.to_dict(orient="records"),
                    "analysis_date": os.path.basename(analysis_file)
                    .split("_")[-1]
                    .split(".")[0],
                },
                "timestamp": pd.Timestamp.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error retrieving analysis: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": None,
                "timestamp": pd.Timestamp.now().isoformat(),
            }

    def health_check(self) -> Dict:
        """
        Check if the scanner is functioning properly.
        """
        try:
            # Check data directory exists
            if not os.path.exists(self.data_dir):
                return {"status": "error", "message": "Data directory not found"}

            # Check if we have any data files
            data_files = [f for f in os.listdir(self.data_dir) if f.endswith(".csv")]
            if not data_files:
                return {"status": "warning", "message": "No data files found"}

            # Check if we have recent analysis
            analysis_file = self._get_analysis_filename()
            if not os.path.exists(analysis_file):
                return {"status": "warning", "message": "No recent analysis found"}

            return {
                "status": "healthy",
                "message": "Scanner operational",
                "data_files": len(data_files),
                "last_analysis": os.path.getmtime(analysis_file),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_trending_stocks(self) -> Dict:
        """
        Get top trending stocks from latest analysis.
        """
        try:
            analysis = self.get_latest_analysis()
            if analysis["status"] == "error":
                return analysis

            strong_trends = analysis["data"]["strong_trends"]
            return {
                "status": "success",
                "message": "Trending stocks retrieved successfully",
                "data": {
                    "stocks": strong_trends,
                    "analysis_date": analysis["data"]["analysis_date"],
                },
                "timestamp": pd.Timestamp.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error getting trending stocks: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": None,
                "timestamp": pd.Timestamp.now().isoformat(),
            }

    def scan_and_analyze(self) -> Dict:
        """
        Perform market scan and analysis in one go.
        Returns formatted results suitable for bot response.
        """
        try:
            self.scan_market()
            results = self.analyze_tickers()

            if results.empty:
                return {
                    "status": "warning",
                    "message": "Scan completed but no results found",
                    "timestamp": pd.Timestamp.now().isoformat(),
                }

            return {
                "status": "success",
                "message": "Market scan completed successfully",
                "data": {
                    "total_stocks": len(results),
                    "analysis_date": pd.Timestamp.now().strftime("%Y%m%d"),
                },
                "timestamp": pd.Timestamp.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"Error in scan and analysis: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": pd.Timestamp.now().isoformat(),
            }

    def get_watchlist_status(self) -> Dict:
        """
        Get current watchlist status.
        """
        return {
            "status": "success",
            "message": "Current watchlist retrieved",
            "data": {"tickers": self.get_tickers(), "total": len(self.tickers)},
            "timestamp": pd.Timestamp.now().isoformat(),
        }


def main():
    """Example usage of MarketScanner demonstrating bot-like commands."""
    scanner = MarketScanner()

    # Example of /scan command
    print("\n=== Market Scan ===")
    scan_result = scanner.scan_and_analyze()
    print(f"Scan Status: {scan_result['status']}")
    print(f"Message: {scan_result['message']}")

    # Example of /trending command
    print("\n=== Trending Stocks ===")
    trending = scanner.get_trending_stocks()
    if trending["status"] == "success":
        for stock in trending["data"]["stocks"]:
            print(f"\nSymbol: {stock['symbol']}")
            print(f"Trend Strength: {stock['trend_strength']:.2f}")
            print(f"Volume Ratio: {stock['volume_ratio']:.2f}")
            print(f"Current Price: ${stock['current_price']:.2f}")

    # Example of /watchlist command
    print("\n=== Watchlist Status ===")
    watchlist = scanner.get_watchlist_status()
    print(f"Total Tickers: {watchlist['data']['total']}")
    print(f"Tickers: {', '.join(watchlist['data']['tickers'])}")


if __name__ == "__main__":
    main()
