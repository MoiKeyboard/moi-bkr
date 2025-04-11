# Algorithmic Trading System

A comprehensive algorithmic trading system that integrates market scanning, technical analysis, and automated trading strategies using Interactive Brokers and Yahoo Finance data providers.

| **Build Status** | **Code Coverage** | **Test Coverage** |
|------------------|-------------------|-------------------|
| [![Build Status](https://github.com/MoiKeyboard/moi-bkr/actions/workflows/build.yml/badge.svg)](https://github.com/MoiKeyboard/moi-bkr/actions/workflows/build.yml) | [![Code Coverage](.github/badges/code_coverage.svg)](https://github.com/MoiKeyboard/moi-bkr/actions/workflows/code-coverage.yml) | ![Test Coverage](.github/badges/test_coverage.svg) |

- [Algorithmic Trading System](#algorithmic-trading-system)
  - [Features](#features)
    - [Market Scanner](#market-scanner)
    - [Trading Strategies](#trading-strategies)
    - [API Endpoints](#api-endpoints)
    - [Telegram Bot](#telegram-bot)
  - [Prerequisites](#prerequisites)
  - [Installation (Python)](#installation-python)
  - [Installation (Docker Container)](#installation-docker-container)
    - [Pull from GitHub Container Registry](#pull-from-github-container-registry)
    - [Run the Container](#run-the-container)
  - [Configuration](#configuration)
  - [Data Provider Setup](#data-provider-setup)
    - [IBKR Trade Workstation settings](#ibkr-trade-workstation-settings)
  - [Project Structure](#project-structure)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Features

### Market Scanner
- Real-time market scanning for trending stocks
- Multiple data provider support (Yahoo Finance, Interactive Brokers)
- Technical indicator analysis (EMA, RSI, Volume, etc.)
- Data persistence with CSV storage
- RESTful API endpoints for scanning results

### Trading Strategies
- Multiple strategy implementations:
  - Moving Average Crossover
  - ATR-based Position Sizing
  - VWAP Trading
  - Enhanced ATR with Multiple Confirmations
- Strategy optimization and backtesting
- Risk management with dynamic position sizing

### API Endpoints
- `/health` - Service health check
- `/scan` - Trigger market scan
- `/trending` - Get trending stocks

### Telegram Bot
- Real-time interaction with the trading system via Telegram
- Commands for market scanning, trending stocks, and system health
- Secure webhook integration with Telegram's API
- User authentication for secure access

| Feature | Status | Notes |
|---------|--------|-------|
| Traefik integration | ✅ Complete | Reverse proxy, TLS, API routing |
| Telegram bot integration | ✅ Complete | Webhook, commands, user authentication |
| Secure data transmission | ✅ Complete | TLS/HTTPS for all endpoints |
| Webhook setup automation | ✅ Complete | Integrated ngrok for local development |
| Docker containerization | ✅ Complete | Multi-container setup with Docker Compose |
| Market scanner API | ✅ Complete | Health, scan, and trending endpoints |
| Bot gateway API | ✅ Complete | Webhook and health endpoints |
| Managed Cloud/VPS deployment | ⏳ Planned | |
| API watchlist functionality | ⏳ Planned | |
| Configuration management | ⏳ In Progress | |
| Environment config management | ⏳ In Progress | |
| Centralized logging | ⏳ Planned | |
| Config.yaml immutability | ⏳ Planned | |

## Prerequisites

- Python 3.12+ (optional if using container)
- Docker (optional if without Python)
- Interactive Brokers TWS or Gateway
- Ngrok (for local webhook development)
- Telegram account (for bot interaction)

## Installation (Python)

1. Clone the repository:
```bash
git clone https://github.com/YourUsername/IBKR.git
cd IBKR
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Installation (Docker Container)

### Pull from GitHub Container Registry

1. Authenticate with GitHub Container Registry:

```bash
# Login to ghcr.io (you'll need a GitHub Personal Access Token with read:packages scope)
echo $GITHUB_PAT | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

2. Pull the container:
```bash
docker pull ghcr.io/moikeyboard/moi-bkr/market-scanner:latest
```

### Run the Container
```bash
cd IBKR
docker run --rm \
  --name market-scanner \
  -p 8000:8000 \
  -e ENV_MODE=prod \
  -v $(pwd)/.data:/app/.data \
  -v $(pwd)/config.yaml:/app/config.yaml \
  ghcr.io/moikeyboard/moi-bkr/market-scanner:latest
```


## Configuration

1. Configure TWS/Gateway settings in `config.yaml`:
```yaml
tws:
  host: "localhost"  # or "host.docker.internal" for Docker
  port: 7497  # 7496 for live, 7497 for paper trading
  client_id: 1
```

2. Set up market analysis configuration:
```yaml
market_analysis:
  provider: yahoo  # or ib
  lookback_days: 100
  tickers:
    - AAPL
    - MSFT
    # Add more tickers...
```

3. Configure Telegram bot in `.env`:
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=<your_bot_token_from_botfather>
TELEGRAM_WEBHOOK_SECRET=<your_webhook_secret>
TELEGRAM_ALLOWED_USERS=<your_numeric_user_id>
# Ngrok URL for local development
NGROK_URL=<your_ngrok_url>
```

1. Generate self-signed certificates
```bash
# Step 1: Generate private key
docker run --rm -v $(pwd)/certs:/certs alpine/openssl genrsa -out /certs/wildcard.key 2048

# Step 2: Generate certificate using the key
docker run --rm -v $(pwd)/certs:/certs alpine/openssl req \
    -x509 \
    -nodes \
    -days 365 \
    -key /certs/wildcard.key \
    -out /certs/wildcard.crt \
    -config /certs/openssl.conf
```

## Data Provider Setup

###  IBKR Trade Workstation settings

1. Open TWS and go to Edit → Global Configuration.
2. Navigate to API → Settings and ensure: 
    - ✅ "Enable ActiveX and Socket Clients" is checked.
    - ✅ "Socket Port" is set (default: 7497 for paper trading, 7496 for live).
    - ✅ "Allow connections from localhost only" is checked (for security).
    - ✅ "Read-Only API" is unchecked (allows position retrieval).
    - ✅ "Enable connection at start-up" is checked.

## Project Structure

```
├── src/
│ ├── analysis/ # Market analysis and data providers
│ ├── api/ # API endpoints
│ ├── bot_gateway/ # Telegram bot integration
│ ├── strategy/ # Trading strategies
│ └── tws/ # Interactive Brokers integration
├── tests/ # Unit test files
├── .github/ # GitHub Actions workflows
├── config.yaml # Configuration file
├── docker-compose.yml # Docker composition
└── requirements.txt # Python dependencies
```

## Documentation

- [Market Scanner API](src/api/README.md) - API endpoints for market scanning

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

lorem ipsum

## Acknowledgments

- Interactive Brokers API
- Yahoo Finance API
- Telegram Bot API
- Traefik for reverse proxy and TLS
- ngrok for local webhook development