# Configuration System Guide
- [Configuration System Guide](#configuration-system-guide)
  - [File Structure](#file-structure)
  - [Key Files](#key-files)
    - [`base.yaml`](#baseyaml)
    - [`base.yaml`](#baseyaml-1)
    - [`Environment Files`](#environment-files)
  - [Usage Examples](#usage-examples)
  - [Setting Up Environments](#setting-up-environments)
  - [Validation](#validation)

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