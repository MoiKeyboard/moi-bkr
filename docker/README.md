# Container Architecture

This directory contains all container-related configurations and documentation for the IBKR trading system.

- [Container Architecture](#container-architecture)
  - [Services](#services)
    - [Market Scanner](#market-scanner)
    - [Telegram Bot](#telegram-bot)
    - [Traefik](#traefik)
  - [Quick Start](#quick-start)
  - [Directory Structure](#directory-structure)
  - [Environment Variables](#environment-variables)
  - [Security](#security)
  - [Troubleshooting](#troubleshooting)

## Services

### Market Scanner
- Main API service for market scanning and analysis
- [Documentation](market-scanner/README.md)

### Telegram Bot
- Bot service for user interaction
- [Documentation](telegram-bot/README.md)

### Traefik
- Reverse proxy and TLS termination
- [Documentation](traefik/README.md)

## Quick Start

1. **Development**
   ```bash
   # Start all services
   docker compose up -d

   # View logs
   docker compose logs -f
   ```

2. **Production**
   ```bash
   # Set domain
   export DOMAIN=your-domain.com

   # Deploy
   ./tools/scripts/deploy.sh
   ```

## Directory Structure

```
docker/
├── market-scanner/ # Market scanner service
│ └── Dockerfile
├── telegram-bot/ # Telegram bot service
│ └── Dockerfile
├── README.md # This file
└── docker-compose.yml # Root compose file
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ENV_MODE | Environment mode | dev |
| DOMAIN | Domain name | localhost |
| PORT | Market scanner port | 8000 |
| LOG_LEVEL | Logging level | info |

## Security

- TLS/SSL configuration in [`../certs/`](../certs/) - [Certificate Documentation](../certs/README.md)
- Environment secrets managed by `Secrets OPerationS` - [SOPS](../config/README.md#secret-management-with-secrets-operations-sops)
- Security headers configured in Traefik

## Troubleshooting

See individual service documentation for specific issues:
- [Market Scanner](market-scanner/README.md#troubleshooting)
- [Telegram Bot](telegram-bot/README.md#troubleshooting)
- [Traefik](traefik/README.md#troubleshooting)