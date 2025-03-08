import yaml
from typing import Dict, List
import pandas as pd
from .data_providers.yahoo_provider import YahooFinanceProvider
from .data_providers.ib_provider import IBDataProvider
import os
import logging
from src.strategy.indicators import TechnicalIndicators


class MarketScanner:
    """Scanner to identify trending stocks using configured data provider."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize scanner with configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = config_path
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configuration
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        self.market_config = config.get("market_analysis", {})
        self.tws_config = config.get("tws", {})
        
        # Set up data directory from config, with default fallback
        self.data_dir = self.market_config.get("data_dir", ".data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize data provider and settings
        self.provider = self._create_provider()
        self.lookback = self.market_config.get("lookback_days", 100)
        self.tickers = self.market_config.get("tickers", [])

    def add_tickers(self, new_tickers: List[str]) -> None:
        """
        Add new tickers to the watchlist.
        
        Args:
            new_tickers: List of ticker symbols to add
        """
        # Convert to uppercase and remove duplicates
        new_tickers = [ticker.upper() for ticker in new_tickers]
        
        # Add new tickers
        self.tickers = list(set(self.tickers + new_tickers))
        
        # Update config file
        self._update_config()
        
        self.logger.info(f"Added tickers: {new_tickers}")
        self.logger.info(f"Current watchlist: {self.tickers}")

    def remove_tickers(self, tickers_to_remove: List[str]) -> None:
        """
        Remove tickers from the watchlist.
        
        Args:
            tickers_to_remove: List of ticker symbols to remove
        """
        # Convert to uppercase
        tickers_to_remove = [ticker.upper() for ticker in tickers_to_remove]
        
        # Remove tickers
        self.tickers = [t for t in self.tickers if t not in tickers_to_remove]
        
        # Update config file
        self._update_config()
        
        self.logger.info(f"Removed tickers: {tickers_to_remove}")
        self.logger.info(f"Current watchlist: {self.tickers}")

    def get_tickers(self) -> List[str]:
        """
        Get current list of tickers.
        
        Returns:
            List of current ticker symbols
        """
        return self.tickers

    def _update_config(self) -> None:
        """Update the config file with current tickers."""
        try:
            # Read current config
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update tickers
            config['market_analysis']['tickers'] = self.tickers
            
            # Write updated config
            with open(self.config_path, 'w') as f:
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
            current_date = (current_date - pd.Timedelta(days=days_to_subtract))
        
        date_str = current_date.strftime('%Y%m%d')
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
            current_date = (current_date - pd.Timedelta(days=days_to_subtract))
        
        current_date_str = current_date.strftime('%Y%m%d')
        
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
                    latest_date = df.index[-1].strftime('%Y%m%d')
                    
                    # Skip if data is current (using the adjusted current date)
                    if latest_date >= current_date_str:
                        self.logger.info(f"{ticker}: Data is current (last: {latest_date}, current: {current_date_str}), skipping...")
                        continue
                
                # Fetch new data only if needed
                self.logger.info(f"Fetching data for {ticker}...")
                market_data = self.provider.fetch_data([ticker], self.lookback)
                
                if ticker in market_data:
                    df = market_data[ticker]
                    latest_date = df.index[-1].strftime('%Y%m%d')
                    
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
            if file.startswith("market_analysis_results_") and file != os.path.basename(analysis_file):
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
                if file.endswith('.csv') and file != 'market_analysis_results.csv':
                    if os.path.getmtime(os.path.join(self.data_dir, file)) > analysis_mtime:
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
        current_close = df['Close'].iloc[-1]
        
        # Calculate metrics
        metrics = {
            'symbol': ticker,
            'trend_strength': TechnicalIndicators.calculate_trend_strength(df),
            'volume_ratio': TechnicalIndicators.calculate_volume_ratio(df),
            'price_momentum': TechnicalIndicators.calculate_momentum(df),
            'rsi': df['RSI'].iloc[-1],
            'above_ema20': current_close > df['EMA20'].iloc[-1],
            'above_ema50': current_close > df['EMA50'].iloc[-1],
            'current_price': current_close
        }
        
        return metrics


def main():
    """Example usage of MarketScanner."""
    scanner = MarketScanner()
    
    # First scan market to update/create CSV files
    scanner.scan_market()
    
    # Then analyze the data
    results = scanner.analyze_tickers()

    if results.empty:
        print("No results found. Check if data was properly fetched.")
        return

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
