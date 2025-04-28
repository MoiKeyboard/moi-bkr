# config.py
import os
import yaml
import subprocess
import logging
from pathlib import Path
from typing import Any, Dict
from copy import deepcopy

class Config:
    """Singleton configuration loader and accessor."""

    _instance = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def __init__(self):
        # Only set up logger once per instance
        if not hasattr(self, "logger"):
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get(self, key: str) -> Any:
        """
        Retrieve a configuration value by dot notation.

        Args:
            key (str): Dot-separated key (e.g., "database.host").

        Returns:
            Any: The configuration value.

        Raises:
            KeyError: If the key is not found.
            ValueError: If a required environment variable is missing.
        """
        env_key = key.upper().replace(".", "_")
        if env_key in os.environ:
            self.logger.debug("Retrieved '%s' from environment variables.", env_key)
            return os.environ[env_key]
        try:
            value = self._nested_get(self._env_config, key.split("."))
            self.logger.debug("Retrieved '%s' from loaded configuration.", key)
            return value
        except KeyError:
            self.logger.error("Configuration key '%s' not found.", key)
            raise

    def _initialize(self) -> None:
        """Initialize configuration by loading environment and config files."""
        self.env = os.getenv("APP_ENV", "development")
        self.logger.info("Initializing configuration for environment: %s", self.env)
        self._load_dotenv()
        self._load_and_merge_config()

    def _load_dotenv(self) -> None:
        """
        Load encrypted .env file into environment variables using SOPS.

        Raises:
            Exception: If decryption or loading fails.
        """
        env_file = Path("config/base.env")
        if env_file.exists():
            try:
                self.logger.info("Decrypting secrets from %s using SOPS...", env_file)
                result = subprocess.run(
                    ["sops", "--decrypt", str(env_file)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.logger.debug("Loading decrypted secrets into environment variables...")
                for line in result.stdout.splitlines():
                    if line.strip() and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        os.environ[key.strip()] = value.strip()
                self.logger.info("Secrets loaded successfully from %s.", env_file)
            except subprocess.CalledProcessError:
                self.logger.exception("Failed to decrypt secrets from %s.", env_file)
                raise
            except Exception:
                self.logger.exception("Error loading secrets from %s.", env_file)
                raise

    def _load_and_merge_config(self) -> None:
        """
        Load base and environment-specific configuration, then resolve secrets.
        """
        self.logger.info("Loading base configuration from config/base.yml...")
        with open("config/base.yml") as f:
            self._base = yaml.safe_load(f)

        self._env_config = deepcopy(self._base)
        env_file = f"environments/{self.env}.yml"
        if Path(env_file).exists():
            self.logger.info("Loading environment overrides from %s...", env_file)
            with open(env_file) as f:
                overrides = yaml.safe_load(f)
                self._deep_update(self._env_config, overrides)
                self.logger.info("Environment overrides from %s applied.", env_file)
                # self.logger.debug("Validation would occur here (TODO).")
        else:
            self.logger.warning("No environment override file found for %s. Using base configuration only.", self.env)
        self._resolve_secrets()

    def _resolve_secrets(self) -> None:
        """
        Replace ${VAR} placeholders in config with actual environment variable values.

        Raises:
            ValueError: If a required environment variable is missing.
        """
        self.logger.debug("Resolving secrets in configuration...")
        for key, value in self._iter_deep_items(self._env_config):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                if env_var not in os.environ:
                    self.logger.error("Missing required environment variable: %s", env_var)
                    raise ValueError(f"Missing required environment variable: {env_var}")
                self._nested_set(self._env_config, key.split("."), os.environ[env_var])
                self.logger.debug("Resolved secret for '%s' from environment variable '%s'.", key, env_var)
        self.logger.info("All secrets resolved.")

    @staticmethod
    def _nested_get(d: Dict, keys: list) -> Any:
        """
        Get a value from a nested dictionary using a list of keys.

        Args:
            d (Dict): The dictionary.
            keys (list): List of keys.

        Returns:
            Any: The value.

        Raises:
            KeyError: If any key is missing.
        """
        for key in keys:
            d = d[key]
        return d

    @staticmethod
    def _nested_set(d: Dict, keys: list, value: Any) -> None:
        """
        Set a value in a nested dictionary using a list of keys.

        Args:
            d (Dict): The dictionary.
            keys (list): List of keys.
            value (Any): Value to set.
        """
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value

    @staticmethod
    def _iter_deep_items(d: Dict, parent_key: str = ""):
        """
        Iterate through all items in a nested dictionary, yielding dot-separated keys.

        Args:
            d (Dict): The dictionary.
            parent_key (str): The base key.

        Yields:
            Tuple[str, Any]: Dot-separated key and value.
        """
        for key, value in d.items():
            current_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                yield from Config._iter_deep_items(value, current_key)
            else:
                yield current_key, value

    @staticmethod
    def _deep_update(d: Dict, u: Dict) -> Dict:
        """
        Recursively update a dictionary with another dictionary.

        Args:
            d (Dict): The original dictionary.
            u (Dict): The update dictionary.

        Returns:
            Dict: The updated dictionary.
        """
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = Config._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d