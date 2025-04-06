# Market Scanner Telegram Bot

This is a Telegram bot that interfaces with the Market Scanner API to provide market analysis and trending stocks information.

## Features

- `/scan` - Trigger a market scan
- `/trending` - Get trending stocks
- `/health` - Check system health
- `/help` - Show available commands

## Setup

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use the `/newbot` command to create a new bot
3. Follow the instructions to name your bot
4. Save the API token provided by BotFather

### 2. Configure Webhook

1. Set up a webhook for your bot using the Telegram API:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-domain.com/webhook
   ```

2. Set a secret token for webhook verification:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-domain.com/webhook&secret_token=your_secret_token
   ```

### 3. Configure Environment Variables

Set the following environment variables:

- `TELEGRAM_WEBHOOK_SECRET` - The secret token you set for webhook verification
- `TELEGRAM_ALLOWED_USERS` - Comma-separated list of allowed Telegram user IDs
- `MARKET_API_URL` - URL of the Market Scanner API (default: http://market-scanner:8000)

### 4. Run with Docker Compose

```bash
docker-compose up -d
```

## Architecture

The bot consists of the following components:

1. **Base Bot Platform** (`bots/base_bot.py`) - Abstract base class defining the bot interface
2. **Market Client** (`market_client.py`) - Client for communicating with the Market Scanner API
3. **Telegram Bot** (`bots/telegram_bot.py`) - Implementation of the Telegram bot
4. **FastAPI App** (`app.py`) - Webhook endpoint for receiving Telegram updates

## Development

### Adding New Commands

1. Add a new handler method to the `TelegramBot` class in `bots/telegram_bot.py`
2. Add the command to the `commands` dictionary in the `__init__` method
3. Implement the handler logic

### Testing

```bash
# Test the health endpoint
curl http://localhost:8001/health

# Test the webhook endpoint (replace with your actual data)
curl -X POST http://localhost:8001/webhook \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: your_secret_token" \
  -d '{"message":{"from":{"id":123456789},"chat":{"id":123456789},"text":"/health"}}'
``` 