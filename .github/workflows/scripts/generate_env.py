import argparse
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Set, List, Tuple
import sys

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
            base_config = yaml.safe_load(f) or {}
            print(f"Loaded config from {file_path}: {base_config}")
            return base_config
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def extract_env_vars_from_value(value: Any, env_vars: Set[str]) -> None:
    """
    Recursively extract environment variables from a value.
    
    Args:
        value: The value to extract variables from
        env_vars: Set to store found variables
    """
    if isinstance(value, str):
        matches = re.findall(r'\${([A-Za-z0-9_]+)}', value)
        env_vars.update(matches)
    elif isinstance(value, dict):
        for v in value.values():
            extract_env_vars_from_value(v, env_vars)
    elif isinstance(value, list):
        for item in value:
            extract_env_vars_from_value(item, env_vars)

def get_required_vars(yaml_content: Dict[str, Any]) -> List[str]:
    """
    Get all required environment variables from YAML content.
    
    Args:
        yaml_content: Dictionary containing the YAML contents
        
    Returns:
        Sorted list of required environment variables
    """
    env_vars = set()
    extract_env_vars_from_value(yaml_content, env_vars)
    return sorted(list(env_vars))

def read_existing_env_file(env_file: Path) -> List[str]:
    """
    Read existing env file and preserve its content.
    
    Args:
        env_file: Path to the env file
        
    Returns:
        List of lines from the existing file
    """
    if not env_file.exists():
        print(f"Warning: {env_file} does not exist, creating new file")
        return []
    
    with open(env_file, 'r') as f:
        return [line.rstrip() for line in f]

def process_env_line(line: str, required_vars: Set[str]) -> str:
    """
    Process a single environment variable line.
    
    Args:
        line: The line to process
        required_vars: Set of required variable names
        
    Returns:
        Processed line with appropriate comment if needed
    """
    # Skip empty lines and comments
    if not line or line.startswith('#'):
        return line
    
    # Split line into variable assignment and comment
    parts = line.split('#', 1)
    var_assignment = parts[0].strip()
    existing_comment = parts[1].strip() if len(parts) > 1 else ''
    
    # Extract variable name
    var_name = var_assignment.split('=')[0].strip()
    
    # Log if variable is not referenced in base.yml
    if var_name and var_name not in required_vars:
        print(f"Warning: ${var_name} is not referenced in base.yml")
    
    # If there's an existing comment, ensure there's a space before it
    # if existing_comment:
    #     return f"{var_assignment} # {existing_comment}"
    
    return var_assignment

def update_env_content(existing_lines: List[str], required_vars: Set[str]) -> List[str]:
    """
    Update existing env content with required variables and comments.
    
    Args:
        existing_lines: Existing lines from env file
        required_vars: Set of required variable names
        
    Returns:
        Updated list of lines with all variables sorted
    """
    # Extract header comments (lines before first variable)
    header_lines = []
    var_lines = []
    found_first_var = False
    
    for line in existing_lines:
        if not found_first_var and (not line or line.startswith('#')):
            header_lines.append(line)
        else:
            found_first_var = True
            if line.strip():  # Keep non-empty lines
                var_lines.append(line)
    
    # Create a dictionary of all variables and their full lines
    var_dict = {}
    
    # Process existing variables
    for line in var_lines:
        if not line.startswith('#'):
            var_name = line.split('=')[0].strip()
            if var_name:
                var_dict[var_name] = line
    
    # Add any missing required variables
    for var in required_vars:
        if var not in var_dict:
            var_dict[var] = f"{var}="
    
    # Generate sorted output with appropriate comments
    output_lines = header_lines
    if header_lines and header_lines[-1] != '':
        output_lines.append('')
    
    # Sort and process all variables
    for var in sorted(var_dict.keys()):
        line = process_env_line(var_dict[var], required_vars)
        output_lines.append(line)
    
    return output_lines

def save_env_file(content: List[str], file_path: Path) -> None:
    """
    Save content to env file.
    
    Args:
        content: List of lines to save
        file_path: Path where to save the file
    """
    try:
        old_content = ""
        if file_path.exists():
            with open(file_path, 'r') as f:
                old_content = f.read()
        new_content = '\n'.join(content) + '\n'
        if old_content == new_content:
            print(f"No changes to {file_path}")
        else:
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"Generated {file_path}")
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description='Generate environment files from YAML configuration')
    parser.add_argument('--config-dir', type=str, default='config',
                      help='Directory containing configuration files')
    parser.add_argument('--environment', type=str,
                      help='Environment to generate (e.g., development, production)')
    parser.add_argument('--input-yaml', type=str, default='base.yml',
                      help='Input YAML file name')
    parser.add_argument('--output-dir', type=str,
                      help='Directory for output ENV files')
    return parser.parse_args()

def generate_env(config_dir: Path, environment: str = None, 
                input_yaml: str = 'base.yml', output_dir: str = None) -> int:
    """
    Generate ENV file from YAML configuration.
    Returns 0 on success, 1 on error.
    
    Args:
        config_dir: Path to configuration directory
        environment: Optional environment name (e.g., development, production)
        input_yaml: Name of input YAML file
        output_dir: Optional output directory for ENV files
    """
    config_dir = Path(config_dir)
    output_dir = Path(output_dir) if output_dir else None

    if output_dir is None:
        output_dir = config_dir / 'environments' if environment else config_dir

    yaml_file = config_dir / input_yaml
    if environment:
        env_file = output_dir / f'{environment}.env'
    else:
        env_file = config_dir / 'base.env'

    output_dir.mkdir(parents=True, exist_ok=True)

    base_config = load_yaml(yaml_file)
    if not base_config:
        print(f"Error: {yaml_file} is empty or invalid")  # For summary/logs
        raise ValueError(f"{yaml_file} is empty or invalid")  # For error handling

    required_vars = set(get_required_vars(base_config))
    existing_lines = read_existing_env_file(env_file)
    updated_lines = update_env_content(existing_lines, required_vars)
    save_env_file(updated_lines, env_file)
    print(f"Found {len(required_vars)} required variables")
    return 0  # Explicit success

if __name__ == '__main__':
    try:
        args = parse_args()
        exit_code = generate_env(
            config_dir=args.config_dir,
            environment=args.environment,
            input_yaml=args.input_yaml,
            output_dir=args.output_dir if args.output_dir else None
        )
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
