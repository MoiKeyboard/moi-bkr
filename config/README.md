# Configuration System Guide

- [Configuration System Guide](#configuration-system-guide)
  - [Objectives](#objectives)
  - [File Structure](#file-structure)
  - [Key Files](#key-files)
    - [`base.yml`](#baseyml)
    - [`.sops.yaml`](#sopsyaml)
    - [`base.env`](#baseenv)
    - [`schema.yml`](#schemayml)
    - [`Environment Files`](#environment-files)
  - [Usage Examples](#usage-examples)
  - [Setting Up Environments](#setting-up-environments)
  - [Validation](#validation)
  - [Secret Management with Secrets OPerationS (SOPS)](#secret-management-with-secrets-operations-sops)
    - [Setup Instructions](#setup-instructions)
    - [WSL-Specific Considerations](#wsl-specific-considerations)
    - [Troubleshooting WSL Setup](#troubleshooting-wsl-setup)

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
├── sops.yml # Configuration file for SOPS
├── schema.yml # Validation rules
├── environments/
│ ├── development.yml # Dev overrides (non-secrets)
│ └── production.yml # Prod overrides (non-secrets)
├── development.env # Gitignored secret files
└── production.env # Gitignored secret files
```


## Key Files

### `base.yml`
- Contains all configuration including encrypted secrets
- Secrets are encrypted using SOPS
- Example of encrypted value:
  ```yaml
  api_key: ENC[AES256_GCM,data=...] # Encrypted secret
  ```

### `.sops.yaml`
- SOPS configuration file defining encryption rules
- Specifies which values to encrypt and which keys to use

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

## Secret Management with Secrets OPerationS (SOPS)

### Setup Instructions
To install sops, download one of the pre-built binaries provided for your platform from the artifacts attached to the releases - [SOPS release](https://github.com/getsops/sops/releases)

1. **Install SOPS**:
   ```bash
   # Download SOPS binary
   wget https://github.com/mozilla/sops/releases/download/v3.10.2/sops-v3.10.2.linux.amd64

   # Make binary executable
   chmod +x sops-v3.10.2.linux.amd64

   # Move binary into your PATH
   mkdir -p ~/.local/bin  # Create user-specific bin directory
   mv sops-v3.10.2.linux.amd64 ~/.local/bin/sops

   # Add to PATH if not already there
   echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
   source ~/.bashrc

   # Verify installation
   sops --version
   ```

2. **Generate OpenSSL Keys in WSL**:
   ```bash
   # Navigate to Windows certs directory through WSL path
   cd /mnt/c/Users/qwek3/Workspace/IBKR/certs

   # Generate RSA key pair for SOPS
   openssl genrsa -out sops.key 2048
   openssl rsa -in sops.key -pubout -out sops.pub

   # Set permissions (note: Windows permissions work differently)
   chmod 600 sops.key
   chmod 644 sops.pub
   ```

3. **Configure SOPS**:
   In `config/.sops.yaml`, add provide details for SOPS configuration
   ```yaml
   creation_rules:
     - path_regex: config/.*\.yml$
       pgp: >-
         $(cat certs/sops.pub | base64 -w0)
       encrypted_regex: '^(api_key|password|token|secret|url|allowed_hosts|allowed_users)$'
   ```

4. **Set Up Environment in WSL**:
   ```bash
   # Add to your ~/.bashrc or ~/.zshrc
   echo 'export SOPS_PGP_FP=$(openssl rsa -in /mnt/c/Users/qwek3/Workspace/IBKR/certs/sops.key -pubout -outform DER | sha1sum | cut -d" " -f1)' >> ~/.bashrc
   source ~/.bashrc
   ```

### WSL-Specific Considerations

1. **Path Handling**:
   - Use `/mnt/c/...` paths to access Windows files
   - Consider creating symlinks for frequently accessed directories
   - Be aware of line ending differences (Windows CRLF vs Unix LF)

2. **File Permissions**:
   - WSL and Windows handle permissions differently
   - Key files created in Windows might need permission adjustments in WSL
   - Use `chmod` in WSL context for proper security

3. **Working with Secrets in WSL**:
   ```bash
   # Encrypt values (from WSL)
   cd /mnt/c/Users/qwek3/Workspace/IBKR
   sops -e -i config/base.yml

   # Edit encrypted files
   sops config/base.yml

   # Decrypt for use
   sops -d config/base.yml
   ```

4. **Integration with Existing SSL Setup**:
   ```bash
   # Verify OpenSSL access to existing certificates
   ls -l /mnt/c/Users/qwek3/Workspace/IBKR/certs/wildcard.crt
   ls -l /mnt/c/Users/qwek3/Workspace/IBKR/certs/wildcard.key
   ```

### Troubleshooting WSL Setup

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

3. **OpenSSL Verification**:
   ```bash
   # Verify OpenSSL installation
   openssl version
   
   # Test key generation
   openssl genrsa -out test.key 2048 && rm test.key
   ```