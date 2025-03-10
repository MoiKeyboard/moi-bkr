import unittest
import sys
import os

# Get the absolute path of the project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from src.analysis.market_scanner import MarketScanner

class TestMarketScanner(unittest.TestCase):
    def setUp(self):
        """Initialize scanner and ensure clean state before each test."""
        self.scanner = MarketScanner()
        # Save original tickers for tearDown
        self._original_tickers = self.scanner.get_tickers()
        # Clear all tickers for clean test state
        self.scanner.remove_tickers(self._original_tickers)
        
    def tearDown(self):
        """Restore original state after each test."""
        # Clear any test tickers
        current_tickers = self.scanner.get_tickers()
        self.scanner.remove_tickers(current_tickers)
        # Restore original tickers
        self.scanner.add_tickers(self._original_tickers)

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
        # Verify clean initial state
        self.assertEqual(len(self.scanner.get_tickers()), 0)
        
        # Test adding empty list
        self.scanner.add_tickers([])
        self.assertEqual(len(self.scanner.get_tickers()), 0)
        
        # Test adding invalid values
        self.scanner.add_tickers([None, 123, ""])
        self.assertEqual(len(self.scanner.get_tickers()), 0)
        
        # Test adding new unique tickers
        test_tickers = ["AAPL", "MSFT"]
        self.scanner.add_tickers(test_tickers)
        self.assertEqual(set(self.scanner.get_tickers()), {"AAPL", "MSFT"})
        
        # Test adding duplicates (shouldn't add)
        self.scanner.add_tickers(["AAPL", "aapl", "MSFT"])
        self.assertEqual(set(self.scanner.get_tickers()), {"AAPL", "MSFT"})
        
        # Test removing non-existent
        self.scanner.remove_tickers(["NONEXISTENT"])
        self.assertEqual(set(self.scanner.get_tickers()), {"AAPL", "MSFT"})
        
        # Test removing actual tickers
        self.scanner.remove_tickers(["AAPL", "MSFT"])
        self.assertEqual(len(self.scanner.get_tickers()), 0)

    def test_ticker_case_sensitivity(self):
        """Test ticker symbol case handling."""
        # Verify clean initial state
        self.assertEqual(len(self.scanner.get_tickers()), 0)
        
        # Add lowercase ticker
        self.scanner.add_tickers(["aapl"])
        self.assertEqual(set(self.scanner.get_tickers()), {"AAPL"})
        
        # Try to add same ticker in different cases
        self.scanner.add_tickers(["AAPL", "aapl", "Aapl"])
        self.assertEqual(set(self.scanner.get_tickers()), {"AAPL"})
        
        # Remove using different case
        self.scanner.remove_tickers(["aapl"])
        self.assertEqual(len(self.scanner.get_tickers()), 0)

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