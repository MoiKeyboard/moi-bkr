from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class BotCommand(BaseModel):
    """Base command model"""
    command: str
    user_id: str
    chat_id: str
    args: Optional[str] = None
    timestamp: datetime = datetime.now()

class BotResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()

class BotPlatform(ABC):
    """Abstract base class for bot platforms"""
    
    @abstractmethod
    async def verify_webhook(self, request: Dict[str, Any]) -> bool:
        """
        Verify webhook request authenticity
        Args:
            request: Complete webhook request data
        Returns:
            bool: True if verification passes
        """
        pass
    
    @abstractmethod
    async def parse_command(self, update: Dict[str, Any]) -> BotCommand:
        """
        Parse platform-specific update into common command format
        Args:
            update: Raw update data from platform
        Returns:
            BotCommand: Parsed command request
        """
        pass
    
    @abstractmethod
    async def format_response(self, response: BotResponse) -> str:
        """
        Format response for platform-specific output
        Args:
            response: Command response to format
        Returns:
            str: Formatted response string
        """
        pass
    
    @abstractmethod
    async def is_user_authorized(self, user_id: str) -> bool:
        """
        Check if user is authorized
        Args:
            user_id: User identifier
        Returns:
            bool: True if user is authorized
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check bot and its dependencies health"""
        pass
