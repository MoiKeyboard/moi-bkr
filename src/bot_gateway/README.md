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

### 2. Get Your Telegram User ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Save the numeric ID it provides (this will be your admin ID)

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret
TELEGRAM_ADMIN_ID=your_numeric_user_id

# Market Scanner API Configuration
MARKET_API_URL=http://localhost:8000

# Domain Configuration
DOMAIN=localhost
```

### 4. Local Development Setup

#### Prerequisites
1. Install [ngrok](https://ngrok.com/download)
2. Sign up for a free ngrok account
3. Set up your authtoken:
   ```bash
   ngrok config add-authtoken your_ngrok_authtoken
   ```

#### Start Services

1. Start the services:
   ```bash
   docker-compose up -d
   ```

2. Start ngrok tunnel:
   ```bash
   ngrok http 443
   ```
   Save the generated URL (e.g., `https://xxxx-xx-xx-xxx-xx.ngrok-free.app`)

3. Set up webhook with Telegram:
   ```bash
   # Check current webhook status
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"

   # Set new webhook
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
   -H "Content-Type: application/json" \
   -d '{
       "url": "https://your-ngrok-url/bot/webhook",
       "secret_token": "your_webhook_secret"
   }'
   ```

### 5. Testing

#### Test Health Endpoints
```bash
# Test market scanner
curl -k https://localhost/api/health

# Test bot gateway
curl -k https://localhost/bot/health
```

#### Test Webhook
```bash
# Test webhook with sample command
curl -k -X POST https://localhost/bot/webhook \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: your_webhook_secret" \
  -d '{
    "message": {
      "from": {"id": your_telegram_user_id},
      "chat": {"id": your_telegram_user_id},
      "text": "/health"
    }
  }'
```

#### Monitor Logs
```bash
# Watch Traefik logs
docker logs traefik -f

# Watch bot logs
docker logs telegram-bot -f
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

### Troubleshooting

1. **Webhook not receiving updates**:
   - Verify ngrok is running and tunnel is active
   - Check webhook registration with getWebhookInfo
   - Ensure TELEGRAM_WEBHOOK_SECRET matches in both webhook registration and environment variables

2. **Market API connection issues**:
   - Check if market-scanner container is running
   - Verify the MARKET_API_URL is correct
   - Check Traefik routing for the /api prefix

3. **Authorization issues**:
   - Ensure your Telegram user ID is correct in TELEGRAM_ADMIN_ID
   - Verify the ID is numeric (not username)
   - Check bot logs for authorization errors

4. **SSL/Certificate issues**:
   - For local development, use `-k` flag with curl to ignore certificate warnings
   - These warnings are normal in development environment

### Security Notes

1. Never commit `.env` file or any secrets to version control
2. Use strong, random strings for webhook secrets
3. Keep the list of allowed users minimal
4. Regularly rotate secrets in production

## Production Deployment

For production deployment:
1. Replace ngrok with your actual domain
2. Set up proper SSL certificates
3. Configure proper environment variables
4. Use secure secrets management
5. Set up monitoring and logging 