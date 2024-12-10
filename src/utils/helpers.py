"""
Module containing utility functions and helpers.
"""
from typing import Any, Dict, Optional
from pathlib import Path
import json
import logging
from datetime import datetime, date
import os
from dotenv import load_dotenv


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Desired logging level
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('finance_tracker.log')
        ]
    )


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string into date object.

    Args:
        date_str: Date string in various formats

    Returns:
        Parsed date object or None if invalid
    """
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format amount as currency string.

    Args:
        amount: Numerical amount
        currency: Currency code

    Returns:
        Formatted currency string
    """
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent.parent


def load_environment() -> None:
    """Load environment variables from .env file."""
    env_path = get_project_root() / '.env'
    load_dotenv(env_path)


def get_data_dir() -> Path:
    """
    Get the data directory path.

    Returns:
        Path to data directory
    """
    return get_project_root() / 'data'


def ensure_dir_exists(path: Path) -> None:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path to check/create
    """
    path.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be safe for filesystem.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')

    # Ensure filename is not too long
    max_length = 255
    name, ext = os.path.splitext(filename)
    if len(filename) > max_length:
        return name[:max_length-len(ext)] + ext

    return filename
