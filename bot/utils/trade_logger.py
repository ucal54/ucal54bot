"""
Trade logging utility - logs all trades to CSV
"""
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class TradeLogger:
    """Logs trade information to CSV file"""
    
    def __init__(self, log_file: str = "trades.csv"):
        """
        Initialize trade logger
        
        Args:
            log_file: Path to trade log CSV file
        """
        self.log_file = log_file
        self.fieldnames = [
            'timestamp',
            'symbol',
            'side',
            'type',
            'entry_price',
            'exit_price',
            'quantity',
            'pnl',
            'pnl_pct',
            'fee',
            'reason',
            'duration_minutes'
        ]
        
        # Create file with headers if it doesn't exist
        if not os.path.exists(log_file):
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                writer.writeheader()
    
    def log_trade(self, trade_data: Dict[str, Any]) -> None:
        """
        Log a completed trade to CSV
        
        Args:
            trade_data: Dictionary containing trade information
        """
        # Ensure all required fields are present
        row = {field: trade_data.get(field, '') for field in self.fieldnames}
        
        # Add timestamp if not present
        if not row['timestamp']:
            row['timestamp'] = datetime.now().isoformat()
        
        # Write to CSV
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(row)
    
    def log_entry(self, symbol: str, price: float, quantity: float, side: str = "BUY") -> None:
        """
        Log trade entry
        
        Args:
            symbol: Trading symbol
            price: Entry price
            quantity: Trade quantity
            side: Trade side (BUY/SELL)
        """
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'type': 'ENTRY',
            'entry_price': price,
            'quantity': quantity
        }
        self.log_trade(trade_data)
    
    def log_exit(self, symbol: str, entry_price: float, exit_price: float, 
                 quantity: float, reason: str, duration_minutes: float = 0,
                 fee: float = 0) -> None:
        """
        Log trade exit
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            exit_price: Exit price
            quantity: Trade quantity
            reason: Exit reason (TP/SL/TIME/EMERGENCY)
            duration_minutes: Trade duration in minutes
            fee: Total fees paid
        """
        pnl = (exit_price - entry_price) * quantity - fee
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': 'SELL',
            'type': 'EXIT',
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl': round(pnl, 8),
            'pnl_pct': round(pnl_pct, 2),
            'fee': fee,
            'reason': reason,
            'duration_minutes': round(duration_minutes, 2)
        }
        self.log_trade(trade_data)
