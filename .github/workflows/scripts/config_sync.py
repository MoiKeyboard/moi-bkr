import yaml
from pathlib import Path
from typing import Dict, Any

def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load YAML file with error handling"""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def save_yaml(data: Dict[str, Any], file_path: Path) -> None:
    """Save YAML file with error handling"""
    try:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

def deep_update(base: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively update base configuration with environment overrides.
    Only preserves values that are explicitly different from base.
    """
    result = base.copy()
    
    for key, value in base.items():
        if key in env:
            if isinstance(value, dict) and isinstance(env[key], dict):
                # Recursively update nested dictionaries
                result[key] = deep_update(value, env[key])
            else:
                # Only keep environment value if it's different from base
                if env[key] != value:
                    result[key] = env[key]
                # If they're the same, keep base value (already copied)
    
    # Add any keys that exist in env but not in base
    # This preserves environment-specific settings
    for key, value in env.items():
        if key not in base:
            result[key] = value
            
    return result

def sync_configs():
    config_dir = Path('config')
    base_file = config_dir / 'base.yml'
    env_dir = config_dir / 'environments'
    
    # Ensure directories exist
    env_dir.mkdir(exist_ok=True)
    
    # Load base configuration
    base_config = load_yaml(base_file)
    if not base_config:
        print("Error: base.yml is empty or invalid")
        return
    
    # Process each environment
    for env_name in ['development', 'production']:
        env_file = env_dir / f'{env_name}.yml'
        
        # Load existing environment config if it exists
        existing_config = load_yaml(env_file) if env_file.exists() else {}
        
        # Update configuration while preserving only different values
        updated_config = deep_update(base_config, existing_config)
        
        # Save updated configuration
        save_yaml(updated_config, env_file)
        print(f"Updated {env_name}.yml")

if __name__ == '__main__':
    sync_configs()