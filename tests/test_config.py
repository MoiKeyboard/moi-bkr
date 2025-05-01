import unittest
import os
import sys
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.config.config import Config

class TestConfig(unittest.TestCase):
    def setUp(self):
        """Initialize test environment."""
        Config._instance = None
        os.environ["APP_ENV"] = "test"
        os.environ["DB_PASSWORD"] = "test_password"
        os.environ["API_KEY"] = "test_key"

    def tearDown(self):
        """Clean up test environment."""
        Config._instance = None
        for key in ["APP_ENV", "DB_PASSWORD", "API_KEY", "DATABASE_HOST", "MISSING_VAR"]:
            os.environ.pop(key, None)

    @patch('subprocess.run')
    @patch('yaml.safe_load')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.open')
    def test_basic_config(self, mock_open_func, mock_exists, mock_yaml_load, mock_subprocess):
        """Test basic configuration loading and access."""
        # Mock subprocess (SOPS) call
        mock_subprocess.return_value = MagicMock(
            stdout="DB_PASSWORD=test_password\nAPI_KEY=test_key",
            returncode=0
        )
        
        # Mock YAML config
        test_config = {
            "database": {
                "host": "localhost",
                "password": "${DB_PASSWORD}",
                "port": 5432
            },
            "api": {
                "key": "${API_KEY}",
                "url": "http://api.example.com"
            }
        }
        
        # Setup mocks
        mock_exists.return_value = True
        mock_yaml_load.return_value = test_config
        
        # Create config instance
        config = Config()
        
        # Test basic config access
        self.assertEqual(config.get("database.host"), "localhost")
        self.assertEqual(config.get("database.port"), 5432)
        self.assertEqual(config.get("api.url"), "http://api.example.com")
        
        # Test secret resolution
        self.assertEqual(config.get("database.password"), "test_password")
        self.assertEqual(config.get("api.key"), "test_key")
        
        # Test environment variable override
        os.environ["DATABASE_HOST"] = "testhost"
        self.assertEqual(config.get("database.host"), "testhost")

    @patch('subprocess.run')
    @patch('yaml.safe_load')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.open')
    def test_missing_env_var(self, mock_open_func, mock_exists, mock_yaml_load, mock_subprocess):
        """Test handling of missing environment variables."""
        # Mock subprocess (SOPS) call
        mock_subprocess.return_value = MagicMock(
            stdout="",
            returncode=0
        )
        
        # Mock YAML config with missing environment variable reference
        test_config = {
            "secret": "${MISSING_VAR}"
        }
        
        mock_exists.return_value = True
        mock_yaml_load.return_value = test_config
        
        # Test that creating config with missing env var raises ValueError
        with self.assertRaises(ValueError) as context:
            config = Config()
        
        self.assertEqual(
            str(context.exception),
            "Missing required environment variable: MISSING_VAR"
        )

if __name__ == "__main__":
    unittest.main()
