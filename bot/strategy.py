"""
Trading strategy implementation
Multi-timeframe EMA + RSI + Volume strategy
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging


class TradingStrategy:
    """
    Multi-timeframe trend-following strategy
    
    Entry Rules (LONG only):
    - Price above EMA200 on both timeframes
    - EMA50 > EMA200
    - RSI between 40 and 60
    - Current volume > SMA(20) volume
    - No open position exists
    
    Exit Rules:
    - Take Profit: +1.2%
    - Stop Loss: -0.6%
    - Time-based exit: > 45 minutes
    - Emergency exit: EMA50 crosses below EMA200 on 5m
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize strategy
        
        Args:
            config: Strategy configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Extract parameters
        self.ema_fast = config['strategy']['indicators']['ema_fast']
        self.ema_slow = config['strategy']['indicators']['ema_slow']
        self.rsi_period = config['strategy']['indicators']['rsi_period']
        self.volume_sma = config['strategy']['indicators']['volume_sma']
        
        self.rsi_min = config['strategy']['entry']['rsi_min']
        self.rsi_max = config['strategy']['entry']['rsi_max']
        
        self.take_profit_pct = config['strategy']['exit']['take_profit_pct']
        self.stop_loss_pct = config['strategy']['exit']['stop_loss_pct']
        self.max_duration_minutes = config['strategy']['exit']['max_duration_minutes']
    
    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index
        
        Args:
            df: DataFrame with 'close' column
            period: RSI period (default: 14)
        
        Returns:
            RSI series
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_volume_sma(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Simple Moving Average of volume"""
        return df['volume'].rolling(window=period).mean()
    
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to DataFrame
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with added indicators
        """
        df = df.copy()
        
        # EMAs
        df['ema_fast'] = self.calculate_ema(df, self.ema_fast)
        df['ema_slow'] = self.calculate_ema(df, self.ema_slow)
        
        # RSI
        df['rsi'] = self.calculate_rsi(df, self.rsi_period)
        
        # Volume SMA
        df['volume_sma'] = self.calculate_volume_sma(df, self.volume_sma)
        
        return df
    
    def check_entry_conditions(self, df_fast: pd.DataFrame, df_slow: pd.DataFrame) -> bool:
        """
        Check if entry conditions are met
        
        Args:
            df_fast: Fast timeframe data (5m) with indicators
            df_slow: Slow timeframe data (15m) with indicators
        
        Returns:
            True if all entry conditions are met
        """
        if df_fast is None or df_slow is None:
            return False
        
        if len(df_fast) < max(self.ema_slow, self.rsi_period, self.volume_sma):
            self.logger.warning("Not enough data for indicators")
            return False
        
        # Get latest values from fast timeframe
        latest_fast = df_fast.iloc[-1]
        latest_slow = df_slow.iloc[-1]
        
        # Check if we have valid indicator values
        if pd.isna(latest_fast['ema_fast']) or pd.isna(latest_fast['ema_slow']):
            self.logger.warning("Invalid EMA values on fast timeframe")
            return False
        
        if pd.isna(latest_slow['ema_fast']) or pd.isna(latest_slow['ema_slow']):
            self.logger.warning("Invalid EMA values on slow timeframe")
            return False
        
        # Condition 1: Price above EMA200 on both timeframes
        price_above_ema_fast = latest_fast['close'] > latest_fast['ema_slow']
        price_above_ema_slow = latest_slow['close'] > latest_slow['ema_slow']
        
        # Condition 2: EMA50 > EMA200 on both timeframes
        ema_cross_fast = latest_fast['ema_fast'] > latest_fast['ema_slow']
        ema_cross_slow = latest_slow['ema_fast'] > latest_slow['ema_slow']
        
        # Condition 3: RSI between 40 and 60
        rsi_in_range = self.rsi_min <= latest_fast['rsi'] <= self.rsi_max
        
        # Condition 4: Current volume > SMA(20) volume
        volume_above_avg = latest_fast['volume'] > latest_fast['volume_sma']
        
        # Log conditions
        self.logger.debug(f"Entry conditions check:")
        self.logger.debug(f"  Price > EMA200 (5m): {price_above_ema_fast}")
        self.logger.debug(f"  Price > EMA200 (15m): {price_above_ema_slow}")
        self.logger.debug(f"  EMA50 > EMA200 (5m): {ema_cross_fast}")
        self.logger.debug(f"  EMA50 > EMA200 (15m): {ema_cross_slow}")
        self.logger.debug(f"  RSI in range ({self.rsi_min}-{self.rsi_max}): {rsi_in_range} (RSI={latest_fast['rsi']:.2f})")
        self.logger.debug(f"  Volume > SMA: {volume_above_avg}")
        
        # All conditions must be True
        all_conditions = (
            price_above_ema_fast and
            price_above_ema_slow and
            ema_cross_fast and
            ema_cross_slow and
            rsi_in_range and
            volume_above_avg
        )
        
        return all_conditions
    
    def check_emergency_exit(self, df_fast: pd.DataFrame) -> bool:
        """
        Check if emergency exit conditions are met
        EMA50 crosses below EMA200 on 5m timeframe
        
        Args:
            df_fast: Fast timeframe data (5m) with indicators
        
        Returns:
            True if emergency exit is needed
        """
        if df_fast is None or len(df_fast) < 2:
            return False
        
        latest = df_fast.iloc[-1]
        previous = df_fast.iloc[-2]
        
        # Check for bearish cross (EMA50 crosses below EMA200)
        cross_below = (previous['ema_fast'] >= previous['ema_slow'] and 
                      latest['ema_fast'] < latest['ema_slow'])
        
        if cross_below:
            self.logger.warning("Emergency exit: EMA50 crossed below EMA200 on 5m")
        
        return cross_below
    
    def calculate_tp_sl(self, entry_price: float) -> Dict[str, float]:
        """
        Calculate take profit and stop loss prices
        
        Args:
            entry_price: Entry price
        
        Returns:
            Dictionary with 'take_profit' and 'stop_loss' prices
        """
        take_profit = entry_price * (1 + self.take_profit_pct / 100)
        stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
        
        return {
            'take_profit': take_profit,
            'stop_loss': stop_loss
        }
    
    def should_exit(self, current_price: float, entry_price: float, 
                   duration_minutes: float, df_fast: pd.DataFrame) -> tuple[bool, str]:
        """
        Check if position should be exited
        
        Args:
            current_price: Current market price
            entry_price: Entry price
            duration_minutes: Trade duration in minutes
            df_fast: Fast timeframe data for emergency exit check
        
        Returns:
            Tuple of (should_exit, reason)
        """
        tp_sl = self.calculate_tp_sl(entry_price)
        
        # Check stop loss
        if current_price <= tp_sl['stop_loss']:
            return True, "STOP_LOSS"
        
        # Check take profit
        if current_price >= tp_sl['take_profit']:
            return True, "TAKE_PROFIT"
        
        # Check time-based exit
        if duration_minutes >= self.max_duration_minutes:
            return True, "TIME_EXIT"
        
        # Check emergency exit
        if self.check_emergency_exit(df_fast):
            return True, "EMERGENCY_EXIT"
        
        return False, ""
