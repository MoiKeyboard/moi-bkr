from .market_scanner import MarketScanner


def main():
    """Extract and save historical data for all configured tickers."""
    # Initialize scanner with config
    scanner = MarketScanner()

    # Save data for all tickers
    scanner.save_market_data(output_dir="strategy/historical_data")


if __name__ == "__main__":
    main()
