import os
import sys
import argparse
from dotenv import dotenv_values

def merge_secrets(source_path, target_path, output_path, env_name, preserve_existing=False):
    """
    Merge environment variables from source into target, writing result to output.
    
    Args:
        source_path: Path to source .env file (template)
        target_path: Path to target .env file (existing)
        output_path: Path where to write merged result
        env_name: Environment name for logging
        preserve_existing: If True, keep all existing keys even if not in source
    """
    # Load both files
    source_env = dotenv_values(source_path)
    target_env = dotenv_values(target_path)

    # Track changes
    added = []
    updated = []
    deleted = []

    if preserve_existing:
        # When preserving existing, only add new keys from source
        for key, value in source_env.items():
            if key not in target_env:
                target_env[key] = value
                added.append(key)
    else:
        # Original merge logic for when not preserving existing
        for key, value in source_env.items():
            if key in target_env:
                if target_env[key] == source_env[key]:
                    target_env[key] = value
                    updated.append(key)
                # If different, keep target value (override)
            else:
                target_env[key] = value
                added.append(key)

        # Remove keys not in source
        keys_to_remove = [k for k in target_env if k not in source_env]
        for k in keys_to_remove:
            deleted.append(k)
            del target_env[k]

    # Write to output file (never overwrite inputs)
    with open(output_path, "w") as f:
        for key, value in sorted(target_env.items()):  # Sort for consistency
            f.write(f"{key}={value}\n")

    # Status output
    print(f"Processing {env_name} environment:")
    if added:
        print(f"Added: {', '.join(sorted(added))}")
    if updated:
        print(f"Updated: {', '.join(sorted(updated))}")
    if deleted:
        print(f"Deleted: {', '.join(sorted(deleted))}")
    if not (added or updated or deleted):
        print("No changes.")

    # Exit code: 0 if changes, 10 if no changes
    if added or updated or deleted:
        sys.exit(0)
    else:
        sys.exit(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Merge environment secrets')
    parser.add_argument('--source', required=True, 
                       help='Path to source template .env file')
    parser.add_argument('--target', required=True, 
                       help='Path to existing .env file to merge with')
    parser.add_argument('--output', required=True, 
                       help='Path to write merged result')
    parser.add_argument('--env', required=True, 
                       help='Environment name for logging')
    parser.add_argument('--preserve-existing', action='store_true',
                       help='Keep all existing keys even if not in source')
    
    args = parser.parse_args()
    merge_secrets(args.source, args.target, args.output, args.env, args.preserve_existing)
