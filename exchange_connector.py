"""
Exchange Connector Module
Handles API connections to Binance and Bybit exchanges using CCXT
"""

import ccxt
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ExchangeConnector:
    """Unified connector for cryptocurrency exchanges"""
    
    def __init__(self, exchange_name: str, api_key: str, secret_key: str, testnet: bool = False):
        """
        Initialize exchange connector
        
        Args:
            exchange_name: 'binance' or 'bybit'
            api_key: API key for the exchange
            secret_key: Secret key for the exchange
            testnet: Whether to use testnet (default: False)
        """
        self.exchange_name = exchange_name.lower()
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.exchange = None
        self._initialize_exchange()
    
    def _initialize_exchange(self) -> None:
        """Initialize CCXT exchange instance"""
        try:
            if self.exchange_name == 'binance':
                self.exchange = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.secret_key,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future',
                        'testnet': self.testnet
                    }
                })
            elif self.exchange_name == 'bybit':
                self.exchange = ccxt.bybit({
                    'apiKey': self.api_key,
                    'secret': self.secret_key,
                    'enableRateLimit': True,
                    'options': {
                        'testnet': self.testnet
                    }
                })
            else:
                raise ValueError(f"Unsupported exchange: {self.exchange_name}")
            
            logger.info(f"Initialized {self.exchange_name} connector (testnet={self.testnet})")
        except Exception as e:
            logger.error(f"Failed to initialize {self.exchange_name} exchange: {e}")
            raise
    
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance
        
        Returns:
            Dictionary with balance information
        """
        try:
            balance = self.exchange.fetch_balance()
            return {
                'total': balance.get('total', {}),
                'free': balance.get('free', {}),
                'used': balance.get('used', {})
            }
        except Exception as e:
            logger.error(f"Error fetching balance from {self.exchange_name}: {e}")
            return {}
    
    def get_futures_positions(self) -> List[Dict[str, Any]]:
        """
        Fetch all futures positions
        
        Returns:
            List of standardized position dictionaries
        """
        positions = []
        try:
            # Fetch positions from exchange
            raw_positions = self.exchange.fetch_positions()
            
            for pos in raw_positions:
                # Only include positions with non-zero size
                if float(pos.get('contracts', 0)) != 0:
                    symbol = pos.get('symbol', '')
                    qty = float(pos.get('contracts', 0))
                    entry_price = float(pos.get('entryPrice', 0))
                    mark_price = float(pos.get('markPrice', pos.get('markPrice', entry_price)))
                    
                    # Determine underlying asset
                    underlying = self._extract_underlying(symbol)
                    
                    # Calculate P&L
                    pnl = (mark_price - entry_price) * qty if qty > 0 else (entry_price - mark_price) * abs(qty)
                    
                    position = {
                        'symbol': symbol,
                        'type': 'Future',
                        'qty': qty,
                        'entry_price': entry_price,
                        'current_price': mark_price,
                        'underlying': underlying,
                        'pnl': pnl,
                        'delta': 1.0 if qty > 0 else -1.0,  # Futures have delta of 1 or -1
                        'gamma': 0.0,  # Futures have no gamma
                        'side': 'long' if qty > 0 else 'short'
                    }
                    positions.append(position)
            
            logger.info(f"Fetched {len(positions)} futures positions from {self.exchange_name}")
        except Exception as e:
            logger.error(f"Error fetching futures positions from {self.exchange_name}: {e}")
        
        return positions
    
    def get_options_positions(self) -> List[Dict[str, Any]]:
        """
        Fetch all options positions
        
        Note: Options support varies by exchange. This is a placeholder implementation.
        For Binance, options are typically accessed via different endpoints.
        
        Returns:
            List of standardized position dictionaries
        """
        positions = []
        try:
            # Binance options are accessed via different API
            if self.exchange_name == 'binance':
                # Try to fetch options positions
                # Note: This may require different API endpoints depending on exchange
                # For now, return empty list if not available
                logger.warning(f"Options positions fetching not fully implemented for {self.exchange_name}")
                pass
            elif self.exchange_name == 'bybit':
                # Bybit options support
                logger.warning(f"Options positions fetching not fully implemented for {self.exchange_name}")
                pass
        except Exception as e:
            logger.error(f"Error fetching options positions from {self.exchange_name}: {e}")
        
        return positions
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            Current price or None if error
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker.get('last', 0))
        except Exception as e:
            logger.error(f"Error fetching price for {symbol} from {self.exchange_name}: {e}")
            return None
    
    def get_option_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Parse option symbol to extract details
        
        Args:
            symbol: Option symbol (e.g., 'BTC-50000-C-20260130')
            
        Returns:
            Dictionary with strike, expiry, option_type, underlying
        """
        try:
            # Parse common option symbol formats
            # Format: UNDERLYING-STRIKE-TYPE-EXPIRY or similar
            parts = symbol.split('-')
            
            if len(parts) >= 3:
                underlying = parts[0]
                strike = float(parts[1])
                option_type = 'Call' if parts[2].upper() in ['C', 'CALL'] else 'Put'
                
                # Try to extract expiry date
                expiry = None
                if len(parts) >= 4:
                    expiry_str = parts[3]
                    # Try to parse as date (format: YYYYMMDD)
                    if len(expiry_str) == 8 and expiry_str.isdigit():
                        expiry = f"{expiry_str[:4]}-{expiry_str[4:6]}-{expiry_str[6:8]}"
                
                return {
                    'underlying': underlying,
                    'strike': strike,
                    'option_type': option_type,
                    'expiry': expiry
                }
        except Exception as e:
            logger.error(f"Error parsing option details for {symbol}: {e}")
        
        return None
    
    def _extract_underlying(self, symbol: str) -> str:
        """
        Extract underlying asset from symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Underlying asset (e.g., 'BTC', 'ETH')
        """
        # Remove common suffixes
        symbol = symbol.replace('USDT', '').replace('USD', '').replace('PERP', '')
        
        # Common patterns
        if 'BTC' in symbol:
            return 'BTC'
        elif 'ETH' in symbol:
            return 'ETH'
        else:
            # Return first part of symbol
            return symbol.split('/')[0] if '/' in symbol else symbol[:3]
    
    def test_connection(self) -> bool:
        """
        Test API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            balance = self.get_balance()
            return bool(balance)
        except Exception as e:
            logger.error(f"Connection test failed for {self.exchange_name}: {e}")
            return False

