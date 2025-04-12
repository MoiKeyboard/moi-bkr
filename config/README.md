# Configuration System Guide

- [Configuration System Guide](#configuration-system-guide)
  - [Objectives](#objectives)
  - [File Structure](#file-structure)
  - [Key Files](#key-files)
    - [`base.yaml`](#baseyaml)
    - [`base.yaml`](#baseyaml-1)
    - [`Environment Files`](#environment-files)
  - [Usage Examples](#usage-examples)
  - [Setting Up Environments](#setting-up-environments)
  - [Validation](#validation)

## Objectives

Following the [12-factor app](https://12factor.net/) methodology, our configuration system addresses multiple factors:

1. **Environment-Specific Configuration** (Factor III: Config)
   - Store config in environment variables
   - Keep development, staging, and production configs separate
   - Enable easy environment switching without code changes

2. **Secrets Management** (Factor III: Config)
   - Store credentials in environment variables
   - Use `$VAR` notation for sensitive data
   - Never commit secrets to version control
   - Support per-environment secrets

3. **Config Validation** (Factor V: Build, release, run)
   - Validate configuration at startup
   - Ensure all required values are present
   - Type checking for configuration values
   - Fail fast if configuration is invalid

4. **Logging** (Factor XI: Logs)
   - Log configuration loading and validation
   - Track configuration changes
   - Debug information for configuration issues

5. **Disposability** (Factor IX: Disposability)
   - Fast startup with configuration validation
   - Graceful shutdown preserving configuration state
   - Support for configuration reloading

## File Structure
```
config/
├── base.yaml # Default values with $SECRET markers
├── schema.yaml # Validation rules
├── environments/
│ ├── development.yaml # Dev overrides (non-secrets)
│ └── production.yaml # Prod overrides (non-secrets)
├── development.env # Gitignored secret files
└── production.env # Gitignored secret files
```


## Key Files

### `base.yaml`
- Contains all default configuration
- Use `$VAR` notation for secrets (e.g., `$DB_PASSWORD`)
- Metadata annotations:
```yaml
port: 8000          # @min: 1024 @max: 65535
ssl: false          # @type: boolean
```

### `base.yaml`
schema.yaml
- JSON Schema validation rules
- Marks required secrets:
```yaml
password:
  type: string
  secret: true  # Fails if $VAR not in environment
```

### `Environment Files`
1. `environments/[env].yaml`:
    - Contains complete configuration copy
    - Only override what changes per environment
    - Example:
     ```yaml
     database:
        port: 5433      # Overrides base value
     ```
2. `[env].env`:
    - Stores secrets for each environment
    - Gitignored by default
    - Example:
      ```bash
      DB_PASSWORD=secret123
      ```

## Usage Examples
[Configuration usage in python](src/config/README.md)
```python
from config import Config

cfg = Config()
print(cfg.get("market_analysis.tickers"))  # Gets resolved value
```

## Setting Up Environments
```bash
cp template.env development.env # Edit with real values
echo "DB_PASSWORD=$PROD_SECRET" > developerment.env
```
## Validation
```bash
TODO .........validate on schema.yaml.........
```