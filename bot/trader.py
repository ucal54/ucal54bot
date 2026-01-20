"""
Main trading bot - orchestrates strategy, risk management, and execution
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException

from bot.strategy import TradingStrategy
from bot.risk_manager import RiskManager
from bot.data_fetcher import DataFetcher
from bot.utils.trade_logger import TradeLogger


class Position:
    """Represents an open trading position"""
    
    def __init__(self, symbol: str, entry_price: float, quantity: float,
                 entry_time: datetime, stop_loss: float, take_profit: float):
        self.symbol = symbol
        self.entry_price = entry_price
        self.quantity = quantity
        self.entry_time = entry_time
        self.stop_loss = stop_loss
        self.take_profit = take_profit
    
    def get_duration_minutes(self) -> float:
        """Get position duration in minutes"""
        return (datetime.now() - self.entry_time).total_seconds() / 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return {
            'symbol': self.symbol,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'entry_time': self.entry_time.isoformat(),
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'duration_minutes': self.get_duration_minutes()
        }


class TradingBot:
    """
    Main trading bot class
    
    Responsibilities:
    - Fetch market data
    - Evaluate strategy signals
    - Execute trades (with dry-run mode)
    - Manage open positions
    - Handle errors and reconnection
    """
    
    def __init__(self, config: Dict[str, Any], api_key: str, api_secret: str,
                 dry_run: bool = True, logger: Optional[logging.Logger] = None):
        """
        Initialize trading bot
        
        Args:
            config: Configuration dictionary
            api_key: Binance API key
            api_secret: Binance API secret
            dry_run: If True, simulate trades without executing
            logger: Logger instance
        """
        self.config = config
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize Binance client
        self.client = Client(api_key, api_secret)
        
        # Initialize modules
        self.data_fetcher = DataFetcher(self.client, self.logger)
        self.strategy = TradingStrategy(config, self.logger)
        self.risk_manager = RiskManager(config, self.logger)
        self.trade_logger = TradeLogger(config['paths']['trade_log'])
        
        # Trading state
        self.symbol = config['trading']['symbol']
        self.timeframe_fast = config['strategy']['timeframes']['fast']
        self.timeframe_slow = config['strategy']['timeframes']['slow']
        self.position: Optional[Position] = None
        
        # Get exchange info
        self.min_notional = self.data_fetcher.get_min_notional(self.symbol)
        self.step_size = self.data_fetcher.get_step_size(self.symbol)
        
        self.logger.info(f"Trading bot initialized for {self.symbol}")
        self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE TRADING'}")
        self.logger.info(f"Min notional: {self.min_notional:.2f}")
        self.logger.info(f"Step size: {self.step_size:.8f}")
    
    def execute_market_buy(self, quantity: float) -> Optional[Dict[str, Any]]:
        """
        Execute market buy order
        
        Args:
            quantity: Quantity to buy
        
        Returns:
            Order result or None if failed
        """
        if self.dry_run:
            # Simulate order in dry run mode
            price = self.data_fetcher.get_current_price(self.symbol)
            if price is None:
                return None
            
            self.logger.info(f"[DRY RUN] Market BUY: {quantity:.8f} {self.symbol} @ ${price:.2f}")
            return {
                'symbol': self.symbol,
                'orderId': int(time.time()),
                'price': str(price),
                'executedQty': str(quantity),
                'status': 'FILLED',
                'type': 'MARKET',
                'side': 'BUY'
            }
        
        try:
            order = self.client.order_market_buy(
                symbol=self.symbol,
                quantity=quantity
            )
            self.logger.info(f"Market BUY executed: {order}")
            return order
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error on buy: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error executing buy order: {e}")
            return None
    
    def execute_market_sell(self, quantity: float) -> Optional[Dict[str, Any]]:
        """
        Execute market sell order
        
        Args:
            quantity: Quantity to sell
        
        Returns:
            Order result or None if failed
        """
        if self.dry_run:
            # Simulate order in dry run mode
            price = self.data_fetcher.get_current_price(self.symbol)
            if price is None:
                return None
            
            self.logger.info(f"[DRY RUN] Market SELL: {quantity:.8f} {self.symbol} @ ${price:.2f}")
            return {
                'symbol': self.symbol,
                'orderId': int(time.time()),
                'price': str(price),
                'executedQty': str(quantity),
                'status': 'FILLED',
                'type': 'MARKET',
                'side': 'SELL'
            }
        
        try:
            order = self.client.order_market_sell(
                symbol=self.symbol,
                quantity=quantity
            )
            self.logger.info(f"Market SELL executed: {order}")
            return order
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error on sell: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error executing sell order: {e}")
            return None
    
    def open_position(self) -> bool:
        """
        Attempt to open a new position
        
        Returns:
            True if position was opened successfully
        """
        # Check if we can open a position
        current_positions = 1 if self.position else 0
        if not self.risk_manager.can_open_position(current_positions):
            return False
        
        # Get current price
        current_price = self.data_fetcher.get_current_price(self.symbol)
        if current_price is None:
            self.logger.error("Failed to get current price")
            return False
        
        # Get balance
        balance = self.data_fetcher.get_account_balance("USDT")
        if balance is None:
            self.logger.error("Failed to get account balance")
            return False
        
        self.logger.info(f"Available balance: ${balance:.2f}")
        
        # Calculate TP/SL
        tp_sl = self.strategy.calculate_tp_sl(current_price)
        stop_loss = tp_sl['stop_loss']
        take_profit = tp_sl['take_profit']
        
        # Calculate position size
        quantity = self.risk_manager.calculate_position_size(
            balance=balance,
            entry_price=current_price,
            stop_loss=stop_loss,
            min_notional=self.min_notional,
            step_size=self.step_size
        )
        
        if quantity == 0:
            self.logger.warning("Position size calculated as 0, skipping entry")
            return False
        
        # Validate trade
        is_valid, error_msg = self.risk_manager.validate_trade(
            quantity=quantity,
            price=current_price,
            balance=balance,
            min_notional=self.min_notional
        )
        
        if not is_valid:
            self.logger.error(f"Trade validation failed: {error_msg}")
            return False
        
        # Calculate risk metrics
        metrics = self.risk_manager.calculate_risk_metrics(
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity
        )
        
        self.logger.info(f"Opening position:")
        self.logger.info(f"  Entry: ${current_price:.2f}")
        self.logger.info(f"  Quantity: {quantity:.8f}")
        self.logger.info(f"  Stop Loss: ${stop_loss:.2f} (-{metrics['potential_loss_pct']:.2f}%)")
        self.logger.info(f"  Take Profit: ${take_profit:.2f} (+{metrics['potential_profit_pct']:.2f}%)")
        self.logger.info(f"  Risk/Reward: 1:{metrics['risk_reward_ratio']:.2f}")
        self.logger.info(f"  Risk Amount: ${metrics['risk_amount']:.2f}")
        
        # Execute buy order
        order = self.execute_market_buy(quantity)
        if order is None:
            self.logger.error("Failed to execute buy order")
            return False
        
        # Create position object
        entry_price = float(order['price'])
        executed_qty = float(order['executedQty'])
        
        self.position = Position(
            symbol=self.symbol,
            entry_price=entry_price,
            quantity=executed_qty,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Log to trade logger
        self.trade_logger.log_entry(
            symbol=self.symbol,
            price=entry_price,
            quantity=executed_qty,
            side="BUY"
        )
        
        self.logger.info(f"✅ Position opened: {self.position.to_dict()}")
        return True
    
    def close_position(self, reason: str) -> bool:
        """
        Close the current position
        
        Args:
            reason: Reason for closing (TAKE_PROFIT, STOP_LOSS, TIME_EXIT, EMERGENCY_EXIT)
        
        Returns:
            True if position was closed successfully
        """
        if self.position is None:
            self.logger.warning("No position to close")
            return False
        
        # Get current price
        current_price = self.data_fetcher.get_current_price(self.symbol)
        if current_price is None:
            self.logger.error("Failed to get current price for exit")
            return False
        
        # Execute sell order
        order = self.execute_market_sell(self.position.quantity)
        if order is None:
            self.logger.error("Failed to execute sell order")
            return False
        
        # Calculate results
        exit_price = float(order['price'])
        pnl = (exit_price - self.position.entry_price) * self.position.quantity
        pnl_pct = ((exit_price - self.position.entry_price) / self.position.entry_price) * 100
        duration = self.position.get_duration_minutes()
        
        # Log to trade logger
        self.trade_logger.log_exit(
            symbol=self.symbol,
            entry_price=self.position.entry_price,
            exit_price=exit_price,
            quantity=self.position.quantity,
            reason=reason,
            duration_minutes=duration,
            fee=0  # Fee calculation can be added if needed
        )
        
        self.logger.info(f"❌ Position closed:")
        self.logger.info(f"  Reason: {reason}")
        self.logger.info(f"  Entry: ${self.position.entry_price:.2f}")
        self.logger.info(f"  Exit: ${exit_price:.2f}")
        self.logger.info(f"  PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        self.logger.info(f"  Duration: {duration:.2f} minutes")
        
        # Clear position
        self.position = None
        return True
    
    def check_and_manage_position(self) -> None:
        """Check open position and manage exits"""
        if self.position is None:
            return
        
        # Get current price
        current_price = self.data_fetcher.get_current_price(self.symbol)
        if current_price is None:
            self.logger.error("Failed to get current price")
            return
        
        # Get fast timeframe data for emergency exit check
        df_fast = self.data_fetcher.get_klines(self.symbol, self.timeframe_fast, limit=250)
        if df_fast is not None:
            df_fast = self.strategy.add_indicators(df_fast)
        
        # Check exit conditions
        should_exit, reason = self.strategy.should_exit(
            current_price=current_price,
            entry_price=self.position.entry_price,
            duration_minutes=self.position.get_duration_minutes(),
            df_fast=df_fast
        )
        
        if should_exit:
            self.close_position(reason)
    
    def check_entry_signal(self) -> None:
        """Check for entry signals and open position if conditions met"""
        # Don't check entry if we already have a position
        if self.position is not None:
            return
        
        # Fetch data for both timeframes
        self.logger.debug(f"Fetching market data for {self.symbol}")
        
        df_fast = self.data_fetcher.get_klines(self.symbol, self.timeframe_fast, limit=250)
        df_slow = self.data_fetcher.get_klines(self.symbol, self.timeframe_slow, limit=250)
        
        if df_fast is None or df_slow is None:
            self.logger.error("Failed to fetch market data")
            return
        
        # Add indicators
        df_fast = self.strategy.add_indicators(df_fast)
        df_slow = self.strategy.add_indicators(df_slow)
        
        # Check entry conditions
        if self.strategy.check_entry_conditions(df_fast, df_slow):
            self.logger.info("🎯 Entry signal detected!")
            self.open_position()
        else:
            self.logger.debug("No entry signal")
    
    def run_iteration(self) -> None:
        """Run one iteration of the trading loop"""
        try:
            # First, manage any existing position
            self.check_and_manage_position()
            
            # Then check for new entry signals
            self.check_entry_signal()
            
        except Exception as e:
            self.logger.error(f"Error in trading iteration: {e}", exc_info=True)
    
    def run(self, loop_interval: int = 5) -> None:
        """
        Run the trading bot in a loop
        
        Args:
            loop_interval: Seconds between iterations
        """
        self.logger.info("=" * 60)
        self.logger.info("🚀 Trading bot started")
        self.logger.info(f"Symbol: {self.symbol}")
        self.logger.info(f"Timeframes: {self.timeframe_fast} / {self.timeframe_slow}")
        self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else '⚠️ LIVE TRADING ⚠️'}")
        self.logger.info("=" * 60)
        
        try:
            while True:
                self.run_iteration()
                time.sleep(loop_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, shutting down...")
            
            # Close any open positions before shutting down
            if self.position:
                self.logger.warning("Closing open position before shutdown...")
                self.close_position("SHUTDOWN")
            
            self.logger.info("Bot stopped")
        
        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            
            # Try to close position on fatal error
            if self.position:
                try:
                    self.close_position("ERROR")
                except:
                    pass
