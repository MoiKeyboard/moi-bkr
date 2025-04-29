# Configuration System (Developer Guide)

- [Configuration System (Developer Guide)](#configuration-system-developer-guide)
  - [Usage](#usage)
    - [Basic Access](#basic-access)
    - [Configuration Resolution](#configuration-resolution)
    - [Environment Handling](#environment-handling)
  - [Best Practices](#best-practices)
    - [1. Secret References](#1-secret-references)
    - [2. Type Safety](#2-type-safety)
    - [3. Error Handling](#3-error-handling)
    - [4. Dot Notation Access](#4-dot-notation-access)
  - [Common Issues](#common-issues)
    - [Missing Configuration](#missing-configuration)
    - [Environment Variables](#environment-variables)
    - [Type Conversion](#type-conversion)
  - [Validation (TODO)](#validation-todo)
  - [Further Reading](#further-reading)

A 12-factor compliant configuration system for accessing configuration and secrets. For operational setup and management, see the [Configuration System Operations Guide](../../config/README.md).

## Usage

### Basic Access
```python
from config import Config

# Get singleton instance
config = Config()

# Access configuration values
tickers = config.get("market_analysis.tickers")  # From environment YAML
api_key = config.get("market_api.key")          # Secret from base.env
port = config.get("bot_gateway.port")           # Regular config value
```

### Configuration Resolution
Values are resolved in this order:
1. Environment variables (`os.environ`)
2. Environment-specific configuration (`environments/{env}.yml`)

### Environment Handling
```python
# Set environment before importing Config
os.environ["APP_ENV"] = "development"  # or "production", etc.
config = Config()  # Will load appropriate environment file
```

**Note:**  
Configuration is loaded once when the `Config` singleton is first created.
Two files are used:
- `environments/{env}.yml` - Environment-specific configuration
- `config/base.env` - Encrypted secrets (optional)

If you change environment variables or config files after initialization, you must restart your application to reload the configuration.

## Best Practices

### 1. Secret References
```yaml
# Good - uses environment variable from base.env
api_key: "${API_KEY}"

# Bad - hardcoded secret
api_key: "1234567890"
```

### 2. Type Safety
```python
# Convert to appropriate types
port = int(config.get("server.port"))
debug = bool(config.get("debug", False))
hosts = list(config.get("allowed_hosts", []))
```

### 3. Error Handling
```python
try:
    # Handle missing configuration
    value = config.get("missing.key")
except KeyError:
    value = default_value

try:
    # Handle missing environment variable
    secret = config.get("secret.value")
except ValueError as e:
    logging.error(f"Missing required secret: {e}")
```

### 4. Dot Notation Access
```python
# Nested configuration access
db_host = config.get("database.connection.host")
api_timeout = config.get("services.api.timeout")
```

## Common Issues

### Missing Configuration
```python
# Check if configuration exists before access
if config.get("feature.enabled", False):
    feature_config = config.get("feature.config")
```

### Environment Variables
- Required environment variables must be defined in `config/base.env`
- Environment variables are decrypted using SOPS
- Variables referenced in config must use `${VAR_NAME}` syntax
- Names are automatically converted to uppercase with underscores

### Type Conversion
```python
# Handle potential type conversion errors
try:
    timeout = int(config.get("api.timeout"))
except ValueError:
    timeout = 30  # Default value
```

## Validation (TODO)
Configuration validation will be implemented soon. For now:
- Check required values manually
- Convert types explicitly
- Handle missing values gracefully

## Further Reading
- [Configuration System Operations Guide](../../config/README.md) - For setup, secrets management, and operational concerns
- [12-Factor Configuration](https://12factor.net/config) - Methodology background
