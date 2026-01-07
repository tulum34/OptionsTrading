"""
Greeks Calculator Module
Calculates options Greeks using Black-Scholes model
"""

import math
import logging
from typing import Dict, Optional
from datetime import datetime
from scipy.stats import norm

logger = logging.getLogger(__name__)


class GreeksCalculator:
    """Calculate options Greeks using Black-Scholes model"""
    
    def __init__(self, risk_free_rate: float = 0.05, default_volatility: float = 0.80):
        """
        Initialize Greeks calculator
        
        Args:
            risk_free_rate: Risk-free interest rate (default: 0.05 = 5%)
            default_volatility: Default implied volatility if not provided (default: 0.80 = 80%)
        """
        self.risk_free_rate = risk_free_rate
        self.default_volatility = default_volatility
    
    def calculate_delta(self, spot: float, strike: float, time_to_expiry: float, 
                        volatility: float, option_type: str = 'Call') -> float:
        """
        Calculate Delta (price sensitivity to underlying price change)
        
        Args:
            spot: Current spot price of underlying
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (annualized)
            option_type: 'Call' or 'Put'
            
        Returns:
            Delta value
        """
        if time_to_expiry <= 0:
            # Option expired
            return 0.0
        
        if spot <= 0 or strike <= 0 or volatility <= 0:
            logger.warning(f"Invalid parameters for delta calculation: spot={spot}, strike={strike}, vol={volatility}")
            return 0.0
        
        try:
            d1 = self._calculate_d1(spot, strike, time_to_expiry, volatility)
            
            if option_type.lower() == 'call':
                delta = norm.cdf(d1)
            else:  # Put
                delta = norm.cdf(d1) - 1.0
            
            return delta
        except Exception as e:
            logger.error(f"Error calculating delta: {e}")
            return 0.0
    
    def calculate_gamma(self, spot: float, strike: float, time_to_expiry: float, 
                        volatility: float) -> float:
        """
        Calculate Gamma (delta sensitivity to underlying price change)
        
        Args:
            spot: Current spot price of underlying
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (annualized)
            
        Returns:
            Gamma value
        """
        if time_to_expiry <= 0 or spot <= 0 or strike <= 0 or volatility <= 0:
            return 0.0
        
        try:
            d1 = self._calculate_d1(spot, strike, time_to_expiry, volatility)
            gamma = norm.pdf(d1) / (spot * volatility * math.sqrt(time_to_expiry))
            return gamma
        except Exception as e:
            logger.error(f"Error calculating gamma: {e}")
            return 0.0
    
    def calculate_theta(self, spot: float, strike: float, time_to_expiry: float, 
                        volatility: float, option_type: str = 'Call') -> float:
        """
        Calculate Theta (price sensitivity to time decay)
        Returns negative value (time decay)
        
        Args:
            spot: Current spot price of underlying
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (annualized)
            option_type: 'Call' or 'Put'
            
        Returns:
            Theta value (negative, represents daily decay)
        """
        if time_to_expiry <= 0 or spot <= 0 or strike <= 0 or volatility <= 0:
            return 0.0
        
        try:
            d1 = self._calculate_d1(spot, strike, time_to_expiry, volatility)
            d2 = self._calculate_d2(d1, time_to_expiry, volatility)
            
            # Theta calculation (per day, so divide by 365)
            term1 = -(spot * norm.pdf(d1) * volatility) / (2 * math.sqrt(time_to_expiry))
            term2 = -self.risk_free_rate * strike * math.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(d2)
            
            if option_type.lower() == 'put':
                term2 = -self.risk_free_rate * strike * math.exp(-self.risk_free_rate * time_to_expiry) * norm.cdf(-d2)
            
            theta = (term1 + term2) / 365.0  # Convert to daily theta
            
            return theta
        except Exception as e:
            logger.error(f"Error calculating theta: {e}")
            return 0.0
    
    def calculate_vega(self, spot: float, strike: float, time_to_expiry: float, 
                       volatility: float) -> float:
        """
        Calculate Vega (price sensitivity to volatility change)
        
        Args:
            spot: Current spot price of underlying
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (annualized)
            
        Returns:
            Vega value (per 1% volatility change)
        """
        if time_to_expiry <= 0 or spot <= 0 or strike <= 0 or volatility <= 0:
            return 0.0
        
        try:
            d1 = self._calculate_d1(spot, strike, time_to_expiry, volatility)
            vega = spot * norm.pdf(d1) * math.sqrt(time_to_expiry) / 100.0  # Per 1% vol change
            return vega
        except Exception as e:
            logger.error(f"Error calculating vega: {e}")
            return 0.0
    
    def calculate_all_greeks(self, position_data: Dict) -> Dict[str, float]:
        """
        Calculate all Greeks for a position
        
        Args:
            position_data: Dictionary containing:
                - 'type': 'Option' or 'Future'
                - 'underlying': Asset name (e.g., 'BTC')
                - 'strike': Strike price (for options)
                - 'expiry': Expiry date string (for options)
                - 'option_type': 'Call' or 'Put' (for options)
                - 'current_price': Current underlying price
                - 'volatility': Implied volatility (optional, uses default if not provided)
                
        Returns:
            Dictionary with delta, gamma, theta, vega
        """
        position_type = position_data.get('type', '').lower()
        
        # For futures, Greeks are simple
        if position_type == 'future':
            qty = position_data.get('qty', 0)
            return {
                'delta': 1.0 if qty > 0 else -1.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0
            }
        
        # For options, calculate using Black-Scholes
        if position_type != 'option':
            logger.warning(f"Unknown position type: {position_type}")
            return {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0}
        
        # Get required parameters
        spot = position_data.get('current_price', 0)
        strike = position_data.get('strike', 0)
        expiry_str = position_data.get('expiry')
        option_type = position_data.get('option_type', 'Call')
        volatility = position_data.get('volatility', self.default_volatility)
        
        if spot <= 0 or strike <= 0:
            logger.warning(f"Invalid spot or strike: spot={spot}, strike={strike}")
            return {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0}
        
        # Calculate time to expiry
        time_to_expiry = self._calculate_time_to_expiry(expiry_str)
        
        if time_to_expiry <= 0:
            # Option expired
            return {'delta': 0.0, 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0}
        
        # Calculate all Greeks
        delta = self.calculate_delta(spot, strike, time_to_expiry, volatility, option_type)
        gamma = self.calculate_gamma(spot, strike, time_to_expiry, volatility)
        theta = self.calculate_theta(spot, strike, time_to_expiry, volatility, option_type)
        vega = self.calculate_vega(spot, strike, time_to_expiry, volatility)
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega
        }
    
    def _calculate_d1(self, spot: float, strike: float, time_to_expiry: float, 
                      volatility: float) -> float:
        """Calculate d1 parameter for Black-Scholes"""
        if time_to_expiry <= 0:
            return 0.0
        
        numerator = math.log(spot / strike) + (self.risk_free_rate + (volatility ** 2) / 2) * time_to_expiry
        denominator = volatility * math.sqrt(time_to_expiry)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_d2(self, d1: float, time_to_expiry: float, volatility: float) -> float:
        """Calculate d2 parameter for Black-Scholes"""
        return d1 - volatility * math.sqrt(time_to_expiry)
    
    def _calculate_time_to_expiry(self, expiry_str: Optional[str]) -> float:
        """
        Calculate time to expiry in years
        
        Args:
            expiry_str: Expiry date string (format: 'YYYY-MM-DD')
            
        Returns:
            Time to expiry in years, or 0 if invalid/expired
        """
        if not expiry_str:
            return 0.0
        
        try:
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            current_date = datetime.now()
            
            if expiry_date <= current_date:
                return 0.0  # Expired
            
            time_diff = expiry_date - current_date
            days_to_expiry = time_diff.days + (time_diff.seconds / 86400.0)
            years_to_expiry = days_to_expiry / 365.25
            
            return max(0.0, years_to_expiry)
        except Exception as e:
            logger.error(f"Error calculating time to expiry from {expiry_str}: {e}")
            return 0.0

