import os
import sys
from dotenv import dotenv_values

def merge_secrets(base_env_path, env_env_path, env_name):
    # Load decrypted files
    base_env = dotenv_values(base_env_path)
    env_env = dotenv_values(env_env_path)

    # Track changes
    added = []
    updated = []
    deleted = []

    # Rule 1 & 2: Update if same, keep override if different
    for key, value in base_env.items():
        if key in env_env:
            if env_env[key] == base_env[key]:
                env_env[key] = value  # Update if same
                updated.append(key)
            # If different, keep env_env value (override)
        else:
            env_env[key] = value  # Rule 3: Add new secrets
            added.append(key)

    # Rule 4: Delete removed secrets
    keys_to_remove = [k for k in env_env if k not in base_env]
    for k in keys_to_remove:
        deleted.append(k)
        del env_env[k]

    # Write merged secrets back to env_env_path
    with open(env_env_path, "w") as f:
        for key, value in env_env.items():
            f.write(f"{key}={value}\n")

    # Print verbose output
    print(f"Processing {env_name} environment:")
    if added:
        print(f"Added: {', '.join(added)}")
    if updated:
        print(f"Updated: {', '.join(updated)}")
    if deleted:
        print(f"Deleted: {', '.join(deleted)}")
    if not (added or updated or deleted):
        print("No changes.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python merge_secrets.py <environment>")
        sys.exit(1)

    env = sys.argv[1]
    base_env_path = "/tmp/base.env"
    env_env_path = f"/tmp/{env}.env"

    merge_secrets(base_env_path, env_env_path, env)
