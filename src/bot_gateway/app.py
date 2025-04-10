import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from .bots.telegram_bot import TelegramBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Market Scanner Bot Gateway")

# Load configuration from environment variables
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "your_default_secret")
ALLOWED_USERS = os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")
MARKET_API_URL = os.getenv("MARKET_API_URL", "http://market-scanner:8000")

# Log the expected webhook secret for debugging
logger.info(f"Webhook secret configured as: {WEBHOOK_SECRET}")

# Initialize bot
bot = TelegramBot(
    webhook_secret=WEBHOOK_SECRET,
    allowed_users=ALLOWED_USERS,
    market_api_url=MARKET_API_URL,
    logger=logger
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Bot gateway is running"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Handle Telegram webhook requests
    """
    try:
        # Get request data
        update = await request.json()
        headers = dict(request.headers)

        # Log received update and headers
        logger.info(f"Received update: {update}")
        logger.info(f"Received headers: {headers}")

        # Log the expected secret token
        logger.info(f"Expected webhook secret: {WEBHOOK_SECRET}")

        # Create request object for verification
        webhook_request = {
            "headers": headers,
            "body": update
        }

        # Verify webhook
        if not await bot.verify_webhook(webhook_request):
            logger.warning("Invalid webhook token")
            raise HTTPException(status_code=403, detail="Invalid webhook token")

        # Parse command
        command = await bot.parse_command(update)

        # Log parsed command
        logger.info(f"Parsed command: {command}")

        # Check authorization
        if not await bot.is_user_authorized(command.user_id):
            logger.warning(f"Unauthorized user: {command.user_id}")
            raise HTTPException(status_code=403, detail="User not authorized")

        # Handle command
        handler = bot.commands.get(command.command)
        if not handler:
            return JSONResponse(content={"text": "Unknown command"})

        # Execute command
        response = await handler(command)

        # Format and return response
        formatted_response = await bot.format_response(response)
        return JSONResponse(content={"text": formatted_response})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"text": f"Error processing request: {str(e)}"}
        )
