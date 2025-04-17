# Configuration System Guide

- [Configuration System Guide](#configuration-system-guide)
  - [Objectives](#objectives)
  - [File Structure](#file-structure)
  - [Key Files](#key-files)
    - [`base.yml`](#baseyml)
    - [`base.env`](#baseenv)
    - [`schema.yml`](#schemayml)
    - [`Environment Files`](#environment-files)
  - [Usage Examples](#usage-examples)
  - [Setting Up Environments](#setting-up-environments)
  - [Validation](#validation)
  - [Automated Configuration Sync](#automated-configuration-sync)
    - [Key Features](#key-features)
    - [Workflow Details](#workflow-details)

## Objectives

Following the [12-factor app](https://12factor.net/) methodology, our configuration system addresses multiple factors:

1. **Environment-Specific Configuration** (Factor III: Config)
   - Store config in environment variables
   - Keep development, staging, and production configs separate
   - Enable easy environment switching without code changes

2. **Secrets Management** (Factor III: Config)
   - Store credentials in environment variables
   - Use `${VAR}` notation for sensitive data
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
├── base.env # Default secret template
├── base.yml # Default configuration value
├── schema.yml # Validation rules
├── environments/
│ ├── development.yml # Dev overrides (non-secrets)
│ └── production.yml # Prod overrides (non-secrets)
├── development.env # Gitignored secret files
└── production.env # Gitignored secret files
```


## Key Files

### `base.yml`
- Contains all default configuration
- Use `${VAR}` notation for secrets (e.g., `${DB_PASSWORD}`)
- Template for generating `environments/[env].yml`
- Metadata annotations:
   ```yaml
   port: 8000          # @min: 1024 @max: 65535
   ssl: false          # @type: boolean
   ```

### `base.env`
- Contains all default secrets
- Template for generating `environments/[env].env`

### `schema.yml`
- JSON Schema validation rules
- Marks required secrets:
   ```yaml
   password:
   type: string
   secret: true  # Fails if $VAR not in environment
   ```

### `Environment Files`
1. `environments/[env].yml`:
    - Contains complete configuration copy
    - Only override what changes per environment
    - Example:
      ```yaml
      database:
        port: 5433      # Overrides base value
      ```
2. `environments/[env].env`:
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
cp base.env development.env # Edit with real values
cp base.yml development.yml # Edit with real values
echo "DB_PASSWORD=$PROD_SECRET" > development.env
```
## Validation
```bash
TODO .........validate on schema.yml.........
```

## Automated Configuration Sync

This repository implements automatic synchronization of environment-specific configuration files with changes to the base configuration. When changes are made to `base.yml`, a GitHub Actions workflow automatically:

1. **Formats and lints** all YAML configuration files for consistency
2. **Synchronizes** environment-specific configurations with the base configuration
3. **Creates a pull request** with the synchronized changes
4. **Cleans up** old branches and pull requests

### Key Features

- **Formatting**: All YAML files use double quotes consistently
- **Synchronization**: Environment-specific values are preserved while inheriting updates from base
- **Change Review**: Pull requests include detailed diff information for easy review
- **Automation**: No manual synchronization required, reducing configuration drift

### Workflow Details

The configuration sync workflow is located at [`.github/workflows/config-sync.yml`](https://github.com/MoiKeyboard/moi-bkr/actions/workflows/config-sync.yml) and runs automatically when changes are made to `config/base.yml`.

You can also [manually trigger](https://github.com/MoiKeyboard/moi-bkr/actions/workflows/config-sync.yml) the workflow if needed.