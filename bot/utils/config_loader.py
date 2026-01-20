"""
Configuration loader for the trading bot
"""
import os
import yaml
from typing import Dict, Any
from pathlib import Path


def load_config(config_path: str = "config/config.yml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Configuration dictionary
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please copy config.example.yml to config.yml and update the values."
        )
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required_fields = ['trading', 'strategy', 'risk', 'bot']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration section: {field}")
    
    return config


def load_env_vars() -> Dict[str, str]:
    """
    Load environment variables for API credentials
    
    Returns:
        Dictionary with API credentials
    
    Raises:
        ValueError: If required environment variables are missing
    """
    from dotenv import load_dotenv
    
    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        raise ValueError(
            "Missing Binance API credentials!\n"
            "Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables.\n"
            "You can create a .env file based on .env.example"
        )
    
    return {
        "api_key": api_key,
        "api_secret": api_secret,
        "testnet": os.getenv("BINANCE_TESTNET", "false").lower() == "true"
    }
