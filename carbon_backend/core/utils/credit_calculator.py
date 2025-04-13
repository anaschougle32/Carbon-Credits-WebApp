"""
Utilities for calculating carbon credits based on 
distance traveled and transport mode.
"""

import logging
from decimal import Decimal
from core.models import SystemConfig

logger = logging.getLogger(__name__)

# Default transport mode multipliers
DEFAULT_MODE_MULTIPLIERS = {
    'car': 0,  # No credits for single-occupancy car
    'carpool': 1.5,
    'public_transport': 2.0,
    'bicycle': 3.0,
    'walking': 3.5,
    'work_from_home': 2.0  # Credits for not commuting at all
}

# Default base rate (credits per km)
DEFAULT_BASE_RATE = 0.1


def get_mode_multiplier(transport_mode):
    """
    Get the multiplier for a specific transport mode.
    Attempts to get from database config, falls back to defaults.
    
    Args:
        transport_mode: String representing the transport mode
        
    Returns:
        Decimal multiplier value
    """
    try:
        # Try to get from database
        config_key = f"multiplier_{transport_mode}"
        db_value = SystemConfig.get_value(config_key)
        
        if db_value:
            return Decimal(db_value)
        
        # Fall back to defaults
        return Decimal(DEFAULT_MODE_MULTIPLIERS.get(transport_mode, 0))
    except Exception as e:
        logger.warning(f"Error getting mode multiplier: {str(e)}")
        return Decimal(DEFAULT_MODE_MULTIPLIERS.get(transport_mode, 0))


def get_base_rate():
    """
    Get the base rate for credit calculation.
    Attempts to get from database config, falls back to default.
    
    Returns:
        Decimal base rate value
    """
    try:
        # Try to get from database
        db_value = SystemConfig.get_value("base_credit_rate")
        
        if db_value:
            return Decimal(db_value)
        
        # Fall back to default
        return Decimal(DEFAULT_BASE_RATE)
    except Exception as e:
        logger.warning(f"Error getting base rate: {str(e)}")
        return Decimal(DEFAULT_BASE_RATE)


def calculate_carbon_credits(distance_km, transport_mode):
    """
    Calculate carbon credits based on distance and transport mode.
    Formula: credits = distance * mode_multiplier * base_rate
    
    Args:
        distance_km: Decimal distance in kilometers
        transport_mode: String representing the transport mode
        
    Returns:
        Decimal amount of carbon credits earned
    """
    # Get multiplier for the transport mode
    multiplier = get_mode_multiplier(transport_mode)
    
    # Get base rate per kilometer
    base_rate = get_base_rate()
    
    # Calculate credits
    credits = Decimal(distance_km) * multiplier * base_rate
    
    # Round to 2 decimal places
    return round(credits, 2)


def calculate_carbon_savings(distance_km, transport_mode):
    """
    Calculate carbon savings in kg of CO2 based on distance and transport mode.
    
    Args:
        distance_km: Decimal distance in kilometers
        transport_mode: String representing the transport mode
        
    Returns:
        Decimal amount of carbon savings in kg of CO2
    """
    # Average car emissions per km (in kg of CO2)
    car_emissions_per_km = Decimal('0.192')
    
    # Emissions by transport mode (in kg of CO2 per km)
    emissions_by_mode = {
        'car': car_emissions_per_km,
        'carpool': car_emissions_per_km / 2,  # Assumes 2 people in carpool
        'public_transport': Decimal('0.041'),
        'bicycle': Decimal('0'),
        'walking': Decimal('0'),
        'work_from_home': car_emissions_per_km  # Savings from not driving at all
    }
    
    # Get emissions for selected mode
    mode_emissions = emissions_by_mode.get(transport_mode, Decimal('0'))
    
    # Calculate savings (car emissions minus mode emissions)
    if transport_mode == 'car':
        savings = Decimal('0')
    else:
        savings = (car_emissions_per_km - mode_emissions) * Decimal(distance_km)
    
    # Round to 2 decimal places
    return round(savings, 2) 