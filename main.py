#!/usr/bin/env python3
"""
Binance SPOT Trading Bot
Main entry point
"""
import sys
from pathlib import Path

from bot.utils.logger import setup_logger
from bot.utils.config_loader import load_config, load_env_vars
from bot.trader import TradingBot


def main():
    """Main function"""
    # Setup logger
    logger = setup_logger("TradingBot")
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config("config/config.yml")
        
        # Load environment variables (API keys)
        logger.info("Loading API credentials...")
        env_vars = load_env_vars()
        
        # Create logs directory
        Path(config['paths']['log_dir']).mkdir(parents=True, exist_ok=True)
        
        # Update logger with config settings
        logger = setup_logger(
            "TradingBot",
            log_dir=config['paths']['log_dir'],
            log_level=config['bot']['log_level']
        )
        
        # Initialize bot
        bot = TradingBot(
            config=config,
            api_key=env_vars['api_key'],
            api_secret=env_vars['api_secret'],
            dry_run=config['trading']['dry_run'],
            logger=logger
        )
        
        # Run bot
        loop_interval = config['bot']['loop_interval_seconds']
        bot.run(loop_interval=loop_interval)
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please copy config.example.yml to config.yml and update it")
        sys.exit(1)
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
