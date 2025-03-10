import unittest
import sys
import os

# Get the absolute path of the project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from fastapi.testclient import TestClient
from src.api.scanner_api import app

class TestScannerAPI(unittest.TestCase):
    def setUp(self):
        """Initialize test client."""
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
    
    def test_scan_endpoint(self):
        """Test scan trigger endpoint."""
        response = self.client.post("/scan")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
    
    # def test_watchlist_endpoints(self):
    #     """Test watchlist management endpoints."""
    #     # Test adding tickers
    #     response = self.client.post("/watchlist/add", json=["AAPL", "MSFT"])
    #     self.assertEqual(response.status_code, 200)
        
    #     # Test getting watchlist
    #     response = self.client.get("/watchlist")
    #     self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main() 