"""
Data fetcher - retrieves market data from Binance
"""
import pandas as pd
from typing import Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging


class DataFetcher:
    """Fetches and processes market data from Binance"""
    
    def __init__(self, client: Client, logger: Optional[logging.Logger] = None):
        """
        Initialize data fetcher
        
        Args:
            client: Binance client instance
            logger: Logger instance
        """
        self.client = client
        self.logger = logger or logging.getLogger(__name__)
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> Optional[pd.DataFrame]:
        """
        Fetch kline/candlestick data from Binance
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Kline interval (e.g., '5m', '15m')
            limit: Number of candles to fetch (max 1000)
        
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            df.set_index('timestamp', inplace=True)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error fetching klines: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching klines: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for a symbol
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Current price or None if error
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error fetching price: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching price: {e}")
            return None
    
    def get_account_balance(self, asset: str = "USDT") -> Optional[float]:
        """
        Get account balance for a specific asset
        
        Args:
            asset: Asset symbol (default: USDT)
        
        Returns:
            Available balance or None if error
        """
        try:
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error fetching balance: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """
        Get exchange info for a specific symbol
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Symbol information dictionary or None if error
        """
        try:
            exchange_info = self.client.get_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    return s
            self.logger.error(f"Symbol {symbol} not found")
            return None
        except BinanceAPIException as e:
            self.logger.error(f"Binance API error fetching symbol info: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching symbol info: {e}")
            return None
    
    def get_min_notional(self, symbol: str) -> float:
        """
        Get minimum notional value for a symbol
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Minimum notional value (default: 10.0 if not found)
        """
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            return 10.0  # Default minimum
        
        for f in symbol_info.get('filters', []):
            if f['filterType'] == 'NOTIONAL':
                return float(f.get('minNotional', 10.0))
        
        return 10.0
    
    def get_step_size(self, symbol: str) -> float:
        """
        Get step size (quantity precision) for a symbol
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Step size (default: 0.00001 if not found)
        """
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            return 0.00001
        
        for f in symbol_info.get('filters', []):
            if f['filterType'] == 'LOT_SIZE':
                return float(f.get('stepSize', 0.00001))
        
        return 0.00001
