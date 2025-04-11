import hmac
import logging
from typing import Dict, Any, List, Optional
from .base_bot import BotPlatform, BotCommand, BotResponse
from ..market_client import MarketClient
import datetime

class TelegramBot(BotPlatform):
    """Telegram bot implementation"""
    
    def __init__(
        self,
        webhook_secret: str,
        allowed_users: List[str],
        market_api_url: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Telegram bot
        Args:
            webhook_secret: Secret token for webhook verification
            allowed_users: List of allowed user IDs
            market_api_url: URL of the Market Scanner API
            logger: Optional logger instance
        """
        self.webhook_secret = webhook_secret
        self.allowed_users = set(allowed_users)
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize market client
        self.logger.info(f"Initializing MarketClient with URL: {market_api_url}")
        self.market_client = MarketClient(
            base_url=market_api_url,
            logger=self.logger
        )
        
        # Command mapping
        self.commands = {
            "/scan": self._handle_scan,
            "/trending": self._handle_trending,
            "/health": self._handle_health,
            "/help": self._handle_help
        }

    async def verify_webhook(self, request: Dict[str, Any]) -> bool:
        """
        Verify Telegram webhook request
        Args:
            request: Complete webhook request data
        Returns:
            bool: True if verification passes
        """
        headers = request.get("headers", {})
        token = headers.get("x-telegram-bot-api-secret-token")  # Fixed casing for header key
        
        # Log the incoming secret for debugging
        if token:
            self.logger.info(f"Incoming secret token: {token}")
        else:
            self.logger.warning("Missing webhook secret token")
            return False

        # Verify that the incoming token matches the expected secret
        if not hmac.compare_digest(token, self.webhook_secret):
            self.logger.warning("Webhook secret token mismatch")
            return False
            
        return True

    async def parse_command(self, update: Dict[str, Any]) -> BotCommand:
        """
        Parse Telegram update into command request
        Args:
            update: Raw update data from Telegram
        Returns:
            BotCommand: Parsed command request
        """
        try:
            message = update.get("message", {})
            text = message.get("text", "").split()
            command = text[0] if text else ""
            args = " ".join(text[1:]) if len(text) > 1 else None
            
            return BotCommand(
                command=command,
                user_id=str(message.get("from", {}).get("id")),
                chat_id=str(message.get("chat", {}).get("id")),
                args=args
            )
        except Exception as e:
            self.logger.error(f"Error parsing command: {e}")
            raise ValueError(f"Invalid command format: {e}")

    async def format_response(self, response: BotResponse) -> str:
        """
        Format response for Telegram
        Args:
            response: Command response to format
        Returns:
            str: Formatted response string
        """
        if not response.success:
            return f"❌ Error: {response.message}"
            
        if not response.data:
            return f"✅ {response.message}"
            
        # Format based on command type
        if "trending" in response.data:
            return self._format_trending_response(response.data)
        elif "scan" in response.data:
            return self._format_scan_response(response.data)
        
        return f"✅ {response.message}\n{response.data}"

    async def is_user_authorized(self, user_id: str) -> bool:
        """
        Check if user is authorized
        Args:
            user_id: User identifier
        Returns:
            bool: True if user is authorized
        """
        authorized = user_id in self.allowed_users
        if not authorized:
            self.logger.warning(f"Unauthorized access attempt from user {user_id}")
        return authorized

    def _format_trending_response(self, data: Dict[str, Any]) -> str:
        """Format trending stocks response"""
        stocks = data.get("trending", [])
        if not stocks:
            return "No trending stocks found"
            
        response = "📈 Trending Stocks:\n\n"
        for stock in stocks:
            response += (
                f"*{stock['symbol']}*\n"
                f"Trend Strength: {stock['trend_strength']:.2f}\n"
                f"Price: ${stock['current_price']:.2f}\n"
                f"Volume Ratio: {stock['volume_ratio']:.2f}\n\n"
            )
        return response

    def _format_scan_response(self, data: Dict[str, Any]) -> str:
        """Format market scan response"""
        return (
            f"🔍 Market Scan Complete\n\n"
            f"Total Stocks: {data.get('total_stocks', 0)}\n"
            f"Analysis Date: {data.get('analysis_date', 'N/A')}\n"
            f"Status: {data.get('status', 'unknown')}"
        )

    async def _handle_scan(self, command: BotCommand) -> BotResponse:
        """Handle scan command"""
        self.logger.info("Handling scan command")
        result = await self.market_client.trigger_scan()
        return BotResponse(
            success=result.get("status") == "success",
            message="Market scan completed",
            data=result.get("data")
        )

    async def _handle_trending(self, command: BotCommand) -> BotResponse:
        """Handle trending command"""
        self.logger.info("Handling trending command")
        result = await self.market_client.get_trending()
        return BotResponse(
            success=result.get("status") == "success",
            message="Retrieved trending stocks",
            data=result.get("data")
        )

    async def _handle_health(self, command: BotCommand) -> BotResponse:
        """Handle health check command"""
        self.logger.info("Handling health command")
        result = await self.market_client.health_check()
        return BotResponse(
            success=result.get("status") == "success",
            message="Health check completed",
            data=result
        )

    async def _handle_help(self, command: BotCommand) -> BotResponse:
        """Handle help command"""
        self.logger.info("Handling help command")
        help_text = {
            "commands": {
                "/scan": "Trigger a market scan",
                "/trending": "Get trending stocks",
                "/health": "Check system health",
                "/help": "Show this help message"
            }
        }
        return BotResponse(
            success=True,
            message="Available commands",
            data=help_text
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the bot and market API
        Returns:
            Dict with health status information
        """
        self.logger.info("Performing health check")
        try:
            # Check market API health
            market_status = await self.market_client.health_check()
            
            return {
                "bot": {
                    "status": "healthy",
                    "allowed_users": len(self.allowed_users)
                },
                "market_api": market_status,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "bot": {
                    "status": "error",
                    "message": str(e)
                },
                "market_api": {"status": "unknown"},
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
