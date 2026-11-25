"""telegram-bot-starter: a minimal Telegram bot template."""

from .config import Config, ConfigError, load_config

__all__ = ["Config", "ConfigError", "load_config"]
__version__ = "0.1.0"
