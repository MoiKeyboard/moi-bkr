import unittest
import sys
import os

# Get the absolute path of the project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from src.analysis.market_scanner import MarketScanner

class TestMarketScanner(unittest.TestCase):
    def setUp(self):
        """Initialize scanner before each test."""
        self.scanner = MarketScanner()
        # Use a small set of test tickers
        self.test_tickers = ["AAPL", "MSFT", "GOOGL"]
        
    def test_scanner_initialization(self):
        """Test scanner initializes correctly."""
        self.assertIsNotNone(self.scanner)
        self.assertIsNotNone(self.scanner.data_dir)
        self.assertIsNotNone(self.scanner.provider)
    
    def test_scan_and_analyze(self):
        """Test full scan and analysis workflow."""
        # Run scan and analysis
        result = self.scanner.scan_and_analyze()
        
        # Check result structure
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("timestamp", result)
        
        # Check if successful
        self.assertEqual(result["status"], "success")
    
    def test_watchlist_management(self):
        """Test watchlist management with edge cases."""
        # Store initial state
        initial_tickers = self.scanner.get_tickers()
        
        # Test adding empty list
        self.scanner.add_tickers([])
        self.assertEqual(self.scanner.get_tickers(), initial_tickers)
        
        # Test adding None or invalid types
        self.scanner.add_tickers([None, 123, ""])
        self.assertEqual(self.scanner.get_tickers(), initial_tickers)
        
        # Test adding duplicates
        test_tickers = ["AAPL", "aapl", "MSFT", "MSFT"]
        self.scanner.add_tickers(test_tickers)
        added_tickers = set(self.scanner.get_tickers()) - set(initial_tickers)
        self.assertEqual(added_tickers, {"AAPL", "MSFT"})
        
        # Test removing non-existent tickers
        self.scanner.remove_tickers(["NONEXISTENT"])
        self.assertEqual(set(self.scanner.get_tickers()) - set(initial_tickers), {"AAPL", "MSFT"})
        
        # Test removing empty list
        self.scanner.remove_tickers([])
        self.assertEqual(set(self.scanner.get_tickers()) - set(initial_tickers), {"AAPL", "MSFT"})
        
        # Test removing actual tickers
        self.scanner.remove_tickers(["AAPL", "MSFT"])
        self.assertEqual(self.scanner.get_tickers(), initial_tickers)

    def test_ticker_case_sensitivity(self):
        """Test ticker symbol case handling."""
        initial_tickers = self.scanner.get_tickers()
        
        # Add lowercase ticker
        self.scanner.add_tickers(["aapl"])
        self.assertIn("AAPL", self.scanner.get_tickers())
        
        # Try to add same ticker in different cases
        self.scanner.add_tickers(["AAPL", "aapl", "Aapl"])
        added_count = len(self.scanner.get_tickers()) - len(initial_tickers)
        self.assertEqual(added_count, 1)  # Only one ticker should be added
        
        # Remove using different case
        self.scanner.remove_tickers(["aapl"])
        self.assertNotIn("AAPL", self.scanner.get_tickers())
        
        # Verify back to initial state
        self.assertEqual(self.scanner.get_tickers(), initial_tickers)

    def test_get_trending_stocks(self):
        """Test trending stocks retrieval."""
        # First scan and analyze
        self.scanner.scan_and_analyze()
        
        # Get trending stocks
        result = self.scanner.get_trending_stocks()
        
        # Check result structure
        self.assertIn("status", result)
        self.assertIn("data", result)
        self.assertIn("timestamp", result)

if __name__ == "__main__":
    unittest.main() 