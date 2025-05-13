# Configuration System Guide

- [Configuration System Guide](#configuration-system-guide)
  - [Objectives](#objectives)
  - [File Structure](#file-structure)
  - [Key Files](#key-files)
    - [`base.yml`](#baseyml)
    - [`.sops.yaml`](#sopsyaml)
    - [`base.env`](#baseenv)
    - [`schema.yml` TODO](#schemayml-todo)
    - [`Environment Files`](#environment-files)
  - [Key Workflows](#key-workflows)
  - [Developer Usage Examples](#developer-usage-examples)
  - [Validation](#validation)
  - [Secret Management with Secrets OPerationS (SOPS)](#secret-management-with-secrets-operations-sops)
    - [Setup Instructions](#setup-instructions)
    - [CI/CD Setup with GitHub Actions](#cicd-setup-with-github-actions)
    - [Working with SOPS](#working-with-sops)
    - [Troubleshooting](#troubleshooting)
    - [Handling Encrypted Environment Files in Workflows](#handling-encrypted-environment-files-in-workflows)

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
├── base.env # Default secret template (encrypted)
├── base.yml # Default configuration value
├── .sops.yaml # Configuration file for SOPS
├── schema.yml # Validation rules
└── environments/
    ├── development.yml # Dev overrides (non-secrets)
    ├── production.yml # Prod overrides (non-secrets)
    ├── development.env # Dev secrets (encrypted)
    └── production.env # Prod secrets (encrypted)
```


## Key Files

### `base.yml`
- Contains all default configuration including encrypted secrets
- Secrets are encrypted using SOPS
- Example of encrypted value:
  ```yaml
  market_api:
    url: ${MARKET_API_URL} 
    key: ${MARKET_API_KEY}
  ```

### `.sops.yaml`
- SOPS configuration file defining encryption rules
- Specifies the public keys generated using *age* to use
- More details in [Secret Management with Secrets OPerationS (SOPS)](#secret-management-with-secrets-operations-sops)

### `base.env`
- Contains all default secrets
- Encrypted using [Secret Management with Secrets OPerationS (SOPS)](#secret-management-with-secrets-operations-sops)
- Template for generating `environments/[env].env`

### `schema.yml` TODO
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
    - Encrypted using [Secret Management with Secrets OPerationS (SOPS)](#secret-management-with-secrets-operations-sops)

## Key Workflows
1. `config-sync`
    - [![Config Sync](https://github.com/MoiKeyboard/moi-bkr/actions/workflows/config-sync.yml/badge.svg)](https://github.com/MoiKeyboard/moi-bkr/actions/workflows/config-sync.yml)
    - Auto-triggers when `base.yml` is modified
    - Formats and lints base and environment YAML files
    - Syncs `base.yml` with environment YAML configuration files
    - Creates necessary pull requests to merge into main branch
    - Preserves environment-specific overrides
    - Sorts all configuration keys alphabetically
    - **Note**: Must complete before `config-env` can run

2. `config-env`
    - [![Config Env](https://github.com/MoiKeyboard/moi-bkr/actions/workflows/config-env.yml/badge.svg)](https://github.com/MoiKeyboard/moi-bkr/actions/workflows/config-env.yml)
    - Runs after Config Sync PR is merged to main
    - Generates `base.env` from `base.yml`
    - Creates and manages environment-specific `.env` files
    - Handles encryption/decryption with SOPS
    - Formats and sorts all `.env` files
    - Provides verbose output for changes
    - **Note**: Depends on successful completion of `config-sync`

## Developer Usage Examples
For detailed developer usage and best practices, see the [Configuration System Developer Guide](../src/config/README.md).

Basic example:
```python
from config import Config

cfg = Config()
print(cfg.get("market_analysis.tickers"))  # Gets resolved value
```

## Validation
The configuration system includes several validation steps:

1. **YAML Validation**
   - All YAML files are linted using `yamllint`
   - Files are formatted using `prettier`

2. **Secret Validation**
   - SOPS key validation in CI/CD
   - Environment variable reference validation
   - Required secrets presence check

3. **Schema Validation** (TODO)
   - JSON Schema validation rules
   - Type checking for configuration values
   - Required fields validation

## Secret Management with Secrets OPerationS (SOPS)
SOPS encrypts individual values within structured files (YAML, JSON, ENV, etc.), enabling secure version control of secrets. Key benefits:
- GitOps-friendly: Encrypted secrets can be safely committed to Git, allowing change tracking and collaboration.
- Environment-aware: Supports multi-environment configurations while preserving file readability.
- Toolchain integration: Designed for CI/CD pipelines and infrastructure-as-code workflows.

This project uses SOPS with *age* encryption for managing environment variables and sensitive configurations, combining strong security with GitOps principles.

### Setup Instructions
To install SOPS and *age*, download one of the pre-built binaries provided for your platform from the artifacts attached to the releases 
- [SOPS release](https://github.com/getsops/sops/releases/latest)
- [age release](https://github.com/FiloSottile/age/releases/latest)

1. **Install SOPS & *age***:
   ```bash
   # Download SOPS binary
   wget https://github.com/mozilla/sops/releases/download/v3.10.2/sops-v3.10.2.linux.amd64

   # Download age
   wget https://github.com/FiloSottile/age/releases/latest/download/age-v1.2.1-linux-amd64.tar.gz
   tar xf age-v1.2.1-linux-amd64.tar.gz

   # Move binaries into your PATH
   mkdir -p ~/.local/bin  # Create user-specific bin directory
   chmod -R 755 ~/.local/bin
   mv sops-v3.10.2.linux.amd64 ~/.local/bin/sops
   mv age/age ~/.local/bin/
   mv age/age-keygen ~/.local/bin/

   # Add to PATH if not already there
   echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
   source ~/.bashrc

   # Verify installation
   sops --version
   ```

2. **Generate *age* Keys**:
   ```bash
   # Generate a key pair
   age-keygen -o certs/sops.age
   # This creates a file containing both public and private key
   # Public key starts with "age1"
   # Private key starts with "AGE-SECRET-KEY-"
   ```

3. **Configure SOPS**:
   Create `config/.sops.yaml` with your age public key:
   ```yaml
   creation_rules:
     - path_regex: base\.yml$
       age: age1246nt5k0uh6vhh0kl5u7ne7vtctf6dezwq5dan380zas82muvehs3ckcd5
       encrypted_regex: '^(api_key|password|token|secret|url|allowed_hosts|allowed_users)$'
   ```
4. **Set Up Environment in WSL**:
   ```bash
   # Add to your ~/.bashrc
   echo 'export SOPS_AGE_KEY_FILE=certs/sops.age' >> ~/.bashrc
   source ~/.bashrc
   ```

### CI/CD Setup with GitHub Actions

1. **Add Age Key to GitHub Secrets**:
   - Go to your repository's Settings > Secrets and Variables > Actions
   - Create a new secret named `SOPS_AGE_KEY_FILE`
   - Copy the ENTIRE contents of your `certs/sops.age` file, including comments:
     ```
     # created: YYYY-MM-DDT00:00:00+00:00
     # public key: age1...
     AGE-SECRET-KEY-...
     ```
   - Paste it as the secret value

2. **Key Management**:
   - Keep `certs/sops.age` secure and NEVER commit it to the repository
   - Add `certs/sops.age` to `.gitignore`
   - The public key in `.sops.yaml` must match the key in GitHub secrets
   - If you need to rotate keys, update both `.sops.yaml` and the GitHub secret

3. **Validation**:
   - The [Config Env](#key-workflows) workflow automatically validates the key matches
   - If keys don't match, encryption/decryption will fail
   - Always test key changes in a development environment first

### Working with SOPS
```bash
# Encrypt secrets environment file
sops --config config/.sops.yaml encrypt -i config/base.env

# Edit encrypted secrets environment file variables 
sops --config config/.sops.yaml edit config/base.env

# Decrypt secrets environment file
sops --config config/.sops.yaml decrypt -i config/base.env
```

### Troubleshooting
1. **Permission Issues**:
   ```bash
   # If you encounter permission errors
   sudo chown $USER:$USER ~/.local/bin/sops
   sudo chown $USER:$USER /mnt/c/Users/qwek3/Workspace/IBKR/certs/sops.*
   ```

2. **Path Issues**:
   ```bash
   # Verify SOPS is in PATH
   which sops
   
   # If not found, ensure ~/.local/bin is in PATH
   echo $PATH
   ```

3. **SOPS Environment Variable Conflicts**:
   ```bash
   # Check for conflicting SOPS environment variables
   env | grep -i sops

   # Common issues:
   # - SOPS_PGP_FP will force PGP encryption even with age config
   # - Multiple SOPS_PGP_FP entries in environment
   
   # Clean up environment variables
   unset SOPS_PGP_FP        # Remove PGP configuration
   unset SOPS_GPG_EXEC      # Remove GPG executable path
   unset SOPS_GPG_KEYSERVER # Remove GPG keyserver
   ```

4. **SOPS Configuration Priority**:
   - Environment variables (`SOPS_PGP_FP`) take precedence over `.sops.yaml`
   - PGP keys configured in environment will be used even if *age* is configured
   - To use *age* exclusively:
     - Ensure no PGP environment variables are set
     - Only configure age in `.sops.yaml`
     - Set `SOPS_AGE_KEY_FILE` for decryption

5. **Verifying SOPS Key**:
   ```bash
   # Verify age key is available
   echo $SOPS_AGE_KEY_FILE
   cat $SOPS_AGE_KEY_FILE | grep "^# public key:"
   ```

6. **Common Errors**:
   - "failed to encrypt new data key with master key" → PGP key in environment
   - "no master keys found" → *age* key not configured correctly
   - "could not get data key" → missing or invalid *age* key file

### Handling Encrypted Environment Files in Workflows

The system manages encrypted environment files through a layered approach:

1. **Base Environment (`base.env`)**
   - Contains default secret values for all environments
   - Encrypted using SOPS with age encryption
   - Serves as the template for environment-specific secrets

2. **Environment-Specific Files (`environments/[env].env`)**
   - Contains environment-specific secret overrides
   - Also encrypted using SOPS with age encryption
   - Can override or extend secrets from `base.env`

3. **Workflow Process**
   The following rules are applied when `base.env` is modified:

   a. **Updates to Existing Secrets**
      - If a secret in `base.env` is modified and matches the value in `environments/[env].env`, the environment file is updated
      - If values differ, the environment-specific value is preserved (override)

   b. **New Secrets**
      - When new secrets are added to `base.env`, they are automatically added to environment files with the same value
      - Environment files can later override these values if needed

   c. **Deleted Secrets**
      - If a secret is removed from `base.env`, it is also removed from environment files
      - This ensures consistency across environments

4. **Workflow Steps**
   ```bash
   # 1. Decrypt both files
   sops --config config/.sops.yaml decrypt -i config/base.env > /tmp/base.env
   sops --config config/.sops.yaml decrypt -i config/environments/[env].env > /tmp/[env].env

   # 2. Merge and update environment file
   python merge_secrets.py [env]

   # 3. Re-encrypt environment file
   sops --config config/.sops.yaml encrypt -i /tmp/[env].env > config/environments/[env].env
   ```

5. **Verbose Output**
   The workflow provides detailed feedback about changes:
   ```
   Processing [env] environment:
   Added: NEW_SECRET1, NEW_SECRET2
   Updated: MODIFIED_SECRET1
   Deleted: REMOVED_SECRET1
   ```

6. **Best Practices**
   - Never commit decrypted `.env` files
   - Always use SOPS for encryption/decryption
   - Keep environment-specific overrides in `environments/[env].env`
   - Use `base.env` for default values only
   - Review workflow output for unexpected changes

7. **Security Considerations**
   - All secret operations happen in memory or temporary files
   - Temporary files are immediately removed after use
   - Decrypted values are never committed to version control
   - Each environment's secrets are encrypted with the same age key for consistency
   - **Note**: Temporary files are created in `/tmp` and automatically cleaned up
