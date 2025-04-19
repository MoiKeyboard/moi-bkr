import re
import yaml
from pathlib import Path
from typing import Dict, Any, Set, List, Tuple

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
        List of lines from the existing file, or default header if file doesn't exist
    """
    if not env_file.exists():
        return [
            "# Environment variables for configuration",
            "# Generated from base.yml",
            "# This file serves as a template for environment-specific .env files",
            ""
        ]
    
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
    
    # If variable is not required and doesn't already have the unused comment
    if var_name and var_name not in required_vars:
        if "Variable not referenced in base.yml" not in existing_comment:
            return f"{var_assignment} ## Variable not referenced in base.yml"
        return line
    
    # If there's an existing comment, ensure there's a space before it
    if existing_comment:
        return f"{var_assignment} # {existing_comment}"
    
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
        with open(file_path, 'w') as f:
            f.write('\n'.join(content) + '\n')
        print(f"Generated {file_path}")
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

def generate_base_env() -> None:
    """
    Main function to generate base.env from base.yml environment variables.
    """
    config_dir = Path('config')
    base_yml = config_dir / 'base.yml'
    base_env = config_dir / 'base.env'
    
    # Load base configuration
    base_config = load_yaml(base_yml)
    if not base_config:
        print("Error: base.yml is empty or invalid")
        return
    
    # Get required variables
    required_vars = set(get_required_vars(base_config))
    
    # Read existing content
    existing_lines = read_existing_env_file(base_env)
    
    # Update content
    updated_lines = update_env_content(existing_lines, required_vars)
    
    # Save updated content
    save_env_file(updated_lines, base_env)
    
    # Print summary
    print(f"Found {len(required_vars)} required variables")

if __name__ == '__main__':
    generate_base_env()
