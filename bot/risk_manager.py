"""
Risk management module
Handles position sizing, risk calculation, and trading limits
"""
import math
from typing import Dict, Any, Optional
import logging


class RiskManager:
    """
    Manages trading risk and position sizing
    
    Features:
    - Dynamic position sizing based on stop loss distance
    - Maximum risk per trade enforcement (1% of balance)
    - Respect Binance minNotional and stepSize
    - One position at a time limit
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize risk manager
        
        Args:
            config: Risk configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        self.max_risk_per_trade_pct = config['risk']['max_risk_per_trade_pct']
        self.max_open_positions = config['risk']['max_open_positions']
    
    def calculate_position_size(self, balance: float, entry_price: float, 
                               stop_loss: float, min_notional: float,
                               step_size: float) -> float:
        """
        Calculate position size based on risk management rules
        
        Args:
            balance: Available trading balance (in quote currency, e.g., USDT)
            entry_price: Planned entry price
            stop_loss: Stop loss price
            min_notional: Minimum notional value from exchange
            step_size: Quantity step size from exchange
        
        Returns:
            Position size in base currency (e.g., BTC)
        """
        # Calculate risk amount (max 1% of balance)
        risk_amount = balance * (self.max_risk_per_trade_pct / 100)
        
        # Calculate price distance to stop loss
        price_distance = abs(entry_price - stop_loss)
        
        if price_distance == 0:
            self.logger.error("Invalid stop loss: distance to entry is zero")
            return 0.0
        
        # Calculate position size based on risk
        # risk_amount = quantity * price_distance
        quantity = risk_amount / price_distance
        
        # Round to step size
        quantity = self.round_to_step_size(quantity, step_size)
        
        # Calculate notional value
        notional = quantity * entry_price
        
        # Ensure minimum notional is met
        if notional < min_notional:
            # Increase quantity to meet minimum notional
            quantity = (min_notional / entry_price) * 1.01  # Add 1% buffer
            quantity = self.round_to_step_size(quantity, step_size)
            notional = quantity * entry_price
            
            self.logger.info(f"Position size adjusted to meet min notional: {min_notional:.2f}")
            
            # Check if this exceeds our max risk
            actual_risk = quantity * price_distance
            actual_risk_pct = (actual_risk / balance) * 100
            
            if actual_risk_pct > self.max_risk_per_trade_pct * 1.5:  # 50% tolerance
                self.logger.warning(
                    f"Minimum notional requires {actual_risk_pct:.2f}% risk, "
                    f"exceeds limit of {self.max_risk_per_trade_pct}%"
                )
                return 0.0
        
        # Ensure we have enough balance
        required_balance = notional
        if required_balance > balance * 0.95:  # Use max 95% of balance
            self.logger.warning(f"Insufficient balance: required {required_balance:.2f}, available {balance:.2f}")
            return 0.0
        
        self.logger.info(f"Position size calculated: {quantity:.8f} (notional: {notional:.2f})")
        return quantity
    
    def round_to_step_size(self, quantity: float, step_size: float) -> float:
        """
        Round quantity to exchange step size
        
        Args:
            quantity: Raw quantity
            step_size: Exchange step size
        
        Returns:
            Rounded quantity
        """
        if step_size == 0:
            return quantity
        
        # Calculate precision from step size
        precision = int(round(-math.log(step_size, 10), 0))
        
        # Round down to step size
        factor = 1 / step_size
        return math.floor(quantity * factor) / factor
    
    def can_open_position(self, current_positions: int) -> bool:
        """
        Check if new position can be opened
        
        Args:
            current_positions: Number of currently open positions
        
        Returns:
            True if new position can be opened
        """
        can_open = current_positions < self.max_open_positions
        
        if not can_open:
            self.logger.info(f"Cannot open position: already at max ({self.max_open_positions})")
        
        return can_open
    
    def validate_trade(self, quantity: float, price: float, balance: float,
                      min_notional: float) -> tuple[bool, str]:
        """
        Validate if trade meets all requirements
        
        Args:
            quantity: Trade quantity
            price: Trade price
            balance: Available balance
            min_notional: Minimum notional value
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if quantity <= 0:
            return False, "Invalid quantity: must be greater than 0"
        
        if price <= 0:
            return False, "Invalid price: must be greater than 0"
        
        notional = quantity * price
        
        if notional < min_notional:
            return False, f"Notional value {notional:.2f} below minimum {min_notional:.2f}"
        
        if notional > balance:
            return False, f"Insufficient balance: required {notional:.2f}, available {balance:.2f}"
        
        return True, ""
    
    def calculate_risk_metrics(self, entry_price: float, stop_loss: float,
                               take_profit: float, quantity: float) -> Dict[str, float]:
        """
        Calculate risk/reward metrics for a trade
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            quantity: Position size
        
        Returns:
            Dictionary with risk metrics
        """
        risk_per_unit = abs(entry_price - stop_loss)
        reward_per_unit = abs(take_profit - entry_price)
        
        risk_amount = risk_per_unit * quantity
        reward_amount = reward_per_unit * quantity
        
        risk_reward_ratio = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0
        
        return {
            'risk_per_unit': risk_per_unit,
            'reward_per_unit': reward_per_unit,
            'risk_amount': risk_amount,
            'reward_amount': reward_amount,
            'risk_reward_ratio': risk_reward_ratio,
            'potential_loss_pct': (risk_per_unit / entry_price) * 100,
            'potential_profit_pct': (reward_per_unit / entry_price) * 100
        }
