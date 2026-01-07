"""
Portfolio Manager Module
Aggregates positions from multiple exchanges and calculates portfolio-level metrics
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from exchange_connector import ExchangeConnector
from greeks_calculator import GreeksCalculator

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manages portfolio data across multiple exchanges"""
    
    def __init__(self, binance_connector: ExchangeConnector, 
                 bybit_connector: ExchangeConnector,
                 greeks_calculator: GreeksCalculator):
        """
        Initialize portfolio manager
        
        Args:
            binance_connector: ExchangeConnector instance for Binance
            bybit_connector: ExchangeConnector instance for Bybit
            greeks_calculator: GreeksCalculator instance
        """
        self.binance_connector = binance_connector
        self.bybit_connector = bybit_connector
        self.greeks_calculator = greeks_calculator
        self.all_positions = []
    
    def fetch_all_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch positions from all exchanges
        
        Returns:
            Dictionary with 'binance' and 'bybit' keys containing position lists
        """
        positions = {
            'binance': [],
            'bybit': []
        }
        
        try:
            # Fetch futures positions
            binance_futures = self.binance_connector.get_futures_positions()
            bybit_futures = self.bybit_connector.get_futures_positions()
            
            # Fetch options positions (if available)
            binance_options = self.binance_connector.get_options_positions()
            bybit_options = self.bybit_connector.get_options_positions()
            
            # Combine and process positions
            positions['binance'] = self._process_positions(binance_futures + binance_options, 'binance')
            positions['bybit'] = self._process_positions(bybit_futures + bybit_options, 'bybit')
            
            # Store all positions for calculations
            self.all_positions = positions['binance'] + positions['bybit']
            
            logger.info(f"Fetched {len(positions['binance'])} Binance positions and {len(positions['bybit'])} Bybit positions")
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
        
        return positions
    
    def _process_positions(self, positions: List[Dict], exchange: str) -> List[Dict]:
        """
        Process positions: calculate Greeks and enrich with additional data
        
        Args:
            positions: List of raw position dictionaries
            exchange: Exchange name
            
        Returns:
            List of processed positions with Greeks
        """
        processed = []
        
        for pos in positions:
            try:
                # Get current price for underlying
                underlying = pos.get('underlying', '')
                if underlying:
                    # Try to get current price
                    symbol = f"{underlying}/USDT"
                    current_price = pos.get('current_price')
                    
                    if not current_price:
                        # Try to fetch from exchange
                        if exchange == 'binance':
                            current_price = self.binance_connector.get_current_price(symbol)
                        else:
                            current_price = self.bybit_connector.get_current_price(symbol)
                    
                    if current_price:
                        pos['current_price'] = current_price
                
                # Calculate Greeks
                greeks = self.greeks_calculator.calculate_all_greeks(pos)
                
                # Add Greeks to position
                pos['delta'] = greeks['delta'] * pos.get('qty', 0)  # Position delta
                pos['gamma'] = greeks['gamma'] * abs(pos.get('qty', 0))  # Position gamma
                pos['theta'] = greeks['theta'] * abs(pos.get('qty', 0))  # Position theta
                pos['vega'] = greeks['vega'] * abs(pos.get('qty', 0))  # Position vega
                
                processed.append(pos)
            except Exception as e:
                logger.error(f"Error processing position {pos.get('symbol', 'unknown')}: {e}")
                # Still add position even if Greeks calculation failed
                pos['delta'] = pos.get('delta', 0.0)
                pos['gamma'] = pos.get('gamma', 0.0)
                pos['theta'] = pos.get('theta', 0.0)
                pos['vega'] = pos.get('vega', 0.0)
                processed.append(pos)
        
        return processed
    
    def calculate_portfolio_greeks(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate aggregated Greeks by asset (BTC, ETH)
        
        Returns:
            Dictionary with 'btc' and 'eth' keys, each containing Greeks
        """
        greeks = {
            'btc': {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0},
            'eth': {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0}
        }
        
        for position in self.all_positions:
            underlying = position.get('underlying', '').upper()
            
            if underlying == 'BTC':
                greeks['btc']['delta'] += position.get('delta', 0.0)
                greeks['btc']['gamma'] += position.get('gamma', 0.0)
                greeks['btc']['theta'] += position.get('theta', 0.0)
                greeks['btc']['vega'] += position.get('vega', 0.0)
            elif underlying == 'ETH':
                greeks['eth']['delta'] += position.get('delta', 0.0)
                greeks['eth']['gamma'] += position.get('gamma', 0.0)
                greeks['eth']['theta'] += position.get('theta', 0.0)
                greeks['eth']['vega'] += position.get('vega', 0.0)
        
        return greeks
    
    def calculate_risk_metrics(self) -> Dict[str, Any]:
        """
        Calculate portfolio risk metrics
        
        Returns:
            Dictionary with risk metrics
        """
        # Calculate delta exposure (total portfolio delta)
        portfolio_greeks = self.calculate_portfolio_greeks()
        delta_exposure = portfolio_greeks['btc']['delta'] + portfolio_greeks['eth']['delta']
        
        # Calculate hedge positions (futures only)
        hedge_btc = 0.0
        hedge_eth = 0.0
        
        # Calculate portfolio value and P&L
        portfolio_value = 0.0
        total_pnl = 0.0
        options_notional = 0.0
        futures_notional = 0.0
        
        for position in self.all_positions:
            position_type = position.get('type', '').lower()
            underlying = position.get('underlying', '').upper()
            qty = position.get('qty', 0)
            current_price = position.get('current_price', 0)
            pnl = position.get('pnl', 0)
            
            # Calculate notional values
            notional = abs(qty) * current_price if current_price > 0 else 0
            
            if position_type == 'future':
                futures_notional += notional
                # Hedge positions are futures
                if underlying == 'BTC':
                    hedge_btc += qty
                elif underlying == 'ETH':
                    hedge_eth += qty
            elif position_type == 'option':
                options_notional += notional
            
            portfolio_value += notional
            total_pnl += pnl
        
        # Calculate hedge ratio
        hedge_ratio = 0.0
        if options_notional > 0:
            hedge_ratio = (futures_notional / options_notional) * 100
        
        # Calculate margin used (simplified - would need actual margin data from exchange)
        margin_used = min(100, (futures_notional / max(portfolio_value, 1)) * 100) if portfolio_value > 0 else 0
        
        # Calculate daily P&L percentage
        daily_pnl_pct = (total_pnl / max(portfolio_value, 1)) * 100 if portfolio_value > 0 else 0.0
        
        # Net risk (simplified as total notional)
        net_risk = portfolio_value
        
        return {
            'delta_exposure': delta_exposure,
            'hedge_position': {
                'btc': hedge_btc,
                'eth': hedge_eth
            },
            'net_risk': net_risk,
            'margin_used': margin_used,
            'daily_pnl': total_pnl,
            'daily_pnl_pct': daily_pnl_pct,
            'portfolio_value': portfolio_value,
            'hedge_ratio': hedge_ratio
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get complete dashboard data in the format expected by frontend
        
        Returns:
            Dictionary matching the frontend's expected format
        """
        try:
            # Fetch latest positions
            positions = self.fetch_all_positions()
            
            # Calculate portfolio Greeks
            portfolio_greeks = self.calculate_portfolio_greeks()
            
            # Calculate risk metrics
            risk_metrics = self.calculate_risk_metrics()
            
            # Format positions for frontend (only include required fields)
            formatted_positions = {
                'binance': [
                    {
                        'symbol': pos.get('symbol', ''),
                        'type': pos.get('type', ''),
                        'qty': pos.get('qty', 0),
                        'delta': pos.get('delta', 0.0),
                        'gamma': pos.get('gamma', 0.0),
                        'pnl': pos.get('pnl', 0.0)
                    }
                    for pos in positions['binance']
                ],
                'bybit': [
                    {
                        'symbol': pos.get('symbol', ''),
                        'type': pos.get('type', ''),
                        'qty': pos.get('qty', 0),
                        'delta': pos.get('delta', 0.0),
                        'gamma': pos.get('gamma', 0.0),
                        'pnl': pos.get('pnl', 0.0)
                    }
                    for pos in positions['bybit']
                ]
            }
            
            # Generate recent activity (simplified - would track actual trades)
            recent_activity = self._generate_recent_activity()
            
            # Build dashboard data
            dashboard_data = {
                'btc': portfolio_greeks['btc'],
                'eth': portfolio_greeks['eth'],
                'risk_metrics': risk_metrics,
                'positions': formatted_positions,
                'recent_activity': recent_activity,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return dashboard_data
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            # Return empty/default data on error
            return {
                'btc': {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0},
                'eth': {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0},
                'risk_metrics': {
                    'delta_exposure': 0.0,
                    'hedge_position': {'btc': 0.0, 'eth': 0.0},
                    'net_risk': 0.0,
                    'margin_used': 0.0,
                    'daily_pnl': 0.0,
                    'daily_pnl_pct': 0.0,
                    'portfolio_value': 0.0,
                    'hedge_ratio': 0.0
                },
                'positions': {'binance': [], 'bybit': []},
                'recent_activity': [],
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _generate_recent_activity(self) -> List[Dict[str, str]]:
        """
        Generate recent activity log
        (Simplified - in production, this would track actual trades)
        
        Returns:
            List of activity dictionaries
        """
        # For now, return empty or placeholder activities
        # In production, this would track actual trades from exchanges
        activities = []
        
        if len(self.all_positions) > 0:
            # Add a placeholder activity
            activities.append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'description': f'Portfolio updated: {len(self.all_positions)} positions',
                'status': 'info'
            })
        
        return activities[-5:] if activities else []  # Return last 5

