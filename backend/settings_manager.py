"""
settings_manager.py

Persistent configuration storage for platform connection settings.
Saves and loads organization URL and API token to/from config.json.
"""

import os
import json
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
DEFAULT_CONFIG = {
    "platform": {
        "org_url": None,
        "api_token": None
    }
}


def get_config() -> Dict[str, Any]:
    """Return the entire configuration dictionary."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """Save the entire configuration dictionary to disk."""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        return False


def get_platform_config() -> Dict[str, Optional[str]]:
    """Return platform-specific configuration (org_url, api_token)."""
    config = get_config()
    return config.get("platform", DEFAULT_CONFIG["platform"])


def save_platform_config(org_url: str, api_token: str) -> bool:
    """Save platform configuration to disk."""
    config = get_config()
    config["platform"] = {
        "org_url": org_url,
        "api_token": api_token
    }
    return save_config(config)


def get_env_or_config_value(env_var: str, config_key: str) -> Optional[str]:
    """Return value from environment variable if set, otherwise from config."""
    config_value = get_platform_config().get(config_key)
    if config_value:
        return config_value
    return os.environ.get(env_var)
