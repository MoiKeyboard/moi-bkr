import httpx
import logging
from typing import Dict, Any, Optional

class MarketClient:
    """Client for interacting with Market Scanner API"""
    
    def __init__(
        self,
        base_url: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Market Scanner API client
        Args:
            base_url: Base URL for the API (e.g., 'http://market-scanner:8000')
            logger: Optional logger instance
        """
        self.base_url = base_url.rstrip('/')
        self.logger = logger or logging.getLogger(__name__)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check API health
        Returns:
            Dict containing API response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "error", "message": str(e)}

    async def get_trending(self) -> Dict[str, Any]:
        """
        Get trending stocks
        Returns:
            Dict containing API response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/trending")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.logger.error(f"Get trending failed: {e}")
            return {"status": "error", "message": str(e)}

    async def trigger_scan(self) -> Dict[str, Any]:
        """
        Trigger market scan
        Returns:
            Dict containing API response
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/scan")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.logger.error(f"Trigger scan failed: {e}")
            return {"status": "error", "message": str(e)} 