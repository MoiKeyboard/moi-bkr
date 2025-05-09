import argparse
import yaml
from pathlib import Path
from typing import Dict, Any, OrderedDict

def parse_args():
    """
    Parse command line arguments for configuration sync.
    
    Returns:
        argparse.Namespace: Parsed command line arguments containing:
            - environment: Optional environment name to sync
            - config_dir: Directory containing configuration files
    """
    parser = argparse.ArgumentParser(description='Sync configuration files')
    parser.add_argument('--environment', type=str,
                      help='Environment to sync (e.g., development, production)')
    parser.add_argument('--config-dir', type=str, default='config',
                      help='Directory containing configuration files')
    return parser.parse_args()

def load_yaml(file_path: Path) -> Dict[str, Any]:
    """
    Load and parse a YAML file with error handling.
    
    Args:
        file_path: Path to the YAML file to load
        
    Returns:
        Dict containing the YAML contents, or empty dict if file doesn't exist/is invalid
    """
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def sort_dict_alphabetically(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sort dictionary keys alphabetically.
    
    Args:
        d: Dictionary to sort. Can contain nested dictionaries which will also be sorted.
        
    Returns:
        Dict[str, Any]: New dictionary with all levels of keys sorted alphabetically.
            Non-dictionary values are preserved as is.
    """
    if not isinstance(d, dict):
        return d
        
    result = {}
    for key in sorted(d.keys()):
        if isinstance(d[key], dict):
            result[key] = sort_dict_alphabetically(d[key])
        else:
            result[key] = d[key]
    return result

def save_yaml(data: Dict[str, Any], file_path: Path) -> None:
    """
    Save dictionary to YAML file while preserving format and sorting keys.
    
    Args:
        data: Dictionary to save to YAML file. Will be sorted before saving.
        file_path: Path where to save the YAML file.
        
    Raises:
        Exception: If there's an error writing to the file, with error details in message.
    """
    sorted_data = sort_dict_alphabetically(data)
    try:
        with open(file_path, 'w') as f:
            yaml.dump(sorted_data, f, default_flow_style=False)
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

def deep_update(base: Dict[str, Any], env: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively update base configuration with environment overrides.
    Only preserves environment values that explicitly differ from base.
    
    Args:
        base: Base configuration dictionary from base.yml
        env: Environment-specific configuration dictionary to merge
        
    Returns:
        Dict[str, Any]: Updated configuration dictionary containing:
            - All base configuration values
            - Environment values that differ from base
            - Environment-specific keys not in base
            
    Example:
        >>> base = {'a': 1, 'b': {'c': 2, 'd': 3}}
        >>> env = {'b': {'c': 4, 'e': 5}}
        >>> deep_update(base, env)
        {'a': 1, 'b': {'c': 4, 'd': 3, 'e': 5}}
    """
    result = base.copy()
    
    for key, value in base.items():
        if key in env:
            if isinstance(value, dict) and isinstance(env[key], dict):
                result[key] = deep_update(value, env[key])
            else:
                if env[key] != value:
                    result[key] = env[key]
    
    for key, value in env.items():
        if key not in base:
            result[key] = value
            
    return result

def sync_configs(config_dir: str, environment: str = None) -> None:
    """
    Synchronize configurations using base.yml as template.
    Sorts base.yml and optionally syncs environment-specific configuration.
    
    Args:
        config_dir: Directory containing configuration files.
                   Should contain base.yml and environments subdirectory.
        environment: Optional environment name to sync (e.g., 'development', 'production').
                    If None, only sorts base.yml.
    
    Raises:
        Exception: If base.yml is empty or invalid
        
    Side Effects:
        - Creates environments directory if it doesn't exist
        - Sorts and updates base.yml
        - If environment specified:
            - Creates environment YAML if it doesn't exist
            - Updates environment YAML with values from base.yml
            - Preserves environment-specific overrides
    """
    config_dir = Path(config_dir)
    base_file = config_dir / 'base.yml'
    env_dir = config_dir / 'environments'
    
    # Ensure directories exist
    env_dir.mkdir(exist_ok=True)
    
    # Load and sort base configuration
    base_config = load_yaml(base_file)
    if not base_config:
        print("Error: base.yml is empty or invalid")
        return
    
    # Always sort and save base config
    save_yaml(base_config, base_file)
    print(f"Sorted base.yml alphabetically")
    
    # If environment is specified, sync that environment
    if environment:
        env_file = env_dir / f'{environment}.yml'
        existing_config = load_yaml(env_file) if env_file.exists() else {}
        updated_config = deep_update(base_config, existing_config)
        save_yaml(updated_config, env_file)
        print(f"Updated {environment}.yml")

if __name__ == '__main__':
    args = parse_args()
    sync_configs(args.config_dir, args.environment)