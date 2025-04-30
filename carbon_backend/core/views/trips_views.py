from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from decimal import Decimal
import uuid
import os

from users.models import CustomUser, EmployeeProfile, Location
from trips.models import Trip, CarbonCredit
from django.conf import settings

# Constants for carbon credit calculations
CREDIT_RATES = {
    'car': Decimal('0.5'),  # 0.5 credits per km
    'carpool': Decimal('2.0'),  # 2 credits per km
    'public_transport': Decimal('3.0'),  # 3 credits per km
    'bicycle': Decimal('5.0'),  # 5 credits per km
    'walking': Decimal('6.0'),  # 6 credits per km
    'work_from_home': Decimal('10.0'),  # 10 credits flat
}

# CO2 savings in kg per km by mode
CO2_SAVINGS = {
    'car': Decimal('0.02'),  # Small savings for single occupancy car (more efficient driving)
    'carpool': Decimal('0.12'),  # Savings from multiple people sharing a ride
    'public_transport': Decimal('0.15'),  # Public transportation has lower emissions per passenger
    'bicycle': Decimal('0.20'),  # Cycling has almost no emissions
    'walking': Decimal('0.20'),  # Walking has no emissions
    'work_from_home': Decimal('0.50'),  # Significant savings from not commuting at all
}

# Average speeds in km/h for different transport modes
TRANSPORT_SPEEDS = {
    'car': 50,  # 50 km/h for car
    'carpool': 45,  # 45 km/h for carpool (accounting for pick-ups)
    'public_transport': 30,  # 30 km/h for public transport (including stops)
    'bicycle': 15,  # 15 km/h for bicycle
    'walking': 5,  # 5 km/h for walking
    'work_from_home': 0,  # No travel time for work from home
}

import requests

def get_distance(origin, destination):
    """Get distance between two locations using Google Maps API."""

    try:
        API_KEY = 'AIzaSyDwWRoTtWgjQc--nP3WoZpH6IrpTQ9gw7w'
        origin = "40.748817,-73.985428"      # NYC
        destination = "40.730610,-73.935242" # NYC
        
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={API_KEY}"

        response = requests.get(url)
        data = response.json()
        print("Response data:", data)

        if data['status'] == 'OK':
            # Extract the numeric distance value in meters
            distance_meters = data['routes'][0]['legs'][0]['distance']['value']
            # Convert to kilometers and round to 2 decimal places
            distance_km = round(distance_meters / 1000, 2)
            print(f"Distance: {distance_km} km")
            return distance_km
        else:
            print("Error:", data['status'])
            return 4.6  # Return a fixed numeric value as fallback
    except Exception as e:
        print(f"Exception in get_distance: {str(e)}")
        return 4.6  # Return a fixed numeric value as fallback

@login_required
@user_passes_test(lambda u: u.is_employee)
def create_trip(request):
    """Create a new trip for an employee."""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('employee_trip_log')
    
    try:
        # Get form data
        start_address = request.POST.get('start_address')
        start_latitude = request.POST.get('start_latitude')
        start_longitude = request.POST.get('start_longitude')
        end_address = request.POST.get('end_address')
        end_latitude = request.POST.get('end_latitude')
        end_longitude = request.POST.get('end_longitude')
        transport_mode = request.POST.get('transport_type')
        trip_date_str = request.POST.get('date')
        distance_km = request.POST.get('distance')
        notes = request.POST.get('notes', '')
        
        # Validate required fields
        if not all([start_address, start_latitude, start_longitude, end_address, end_latitude, end_longitude, 
                   transport_mode, trip_date_str, distance_km]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('employee_trip_log')
        
        # Get employee profile
        employee = request.user.employee_profile
        
        # Create start location
        start_location = Location.objects.create(
            name=f"Start Location - {trip_date_str}",
            address=start_address,
            latitude=Decimal(start_latitude),
            longitude=Decimal(start_longitude),
            location_type='trip_start',
            created_by=request.user
        )
        
        # Create end location
        end_location = Location.objects.create(
            name=f"End Location - {trip_date_str}",
            address=end_address,
            latitude=Decimal(end_latitude),
            longitude=Decimal(end_longitude),
            location_type='trip_end',
            created_by=request.user
        )
        
        # Parse date
        trip_date = datetime.strptime(trip_date_str, "%Y-%m-d").date()
        trip_datetime = timezone.make_aware(datetime.combine(trip_date, datetime.min.time()))
        
        # Calculate credits based on transport mode and distance
        distance_km = Decimal(distance_km)
        if transport_mode == 'work_from_home':
            credits_earned = Decimal('10')  # Fixed credits for WFH
            carbon_savings = Decimal('10')  # Fixed carbon savings for WFH
        else:
            mode_factors = {
                'walking': Decimal('6'),
                'bicycle': Decimal('5'),
                'public_transport': Decimal('3'),
                'carpool': Decimal('2'),
                'car': Decimal('0.5')
            }
            factor = mode_factors.get(transport_mode, Decimal('1'))
            credits_earned = distance_km * factor
            carbon_savings = distance_km * factor  # Using same factor for carbon savings
        
        # Create the trip
        trip = Trip.objects.create(
            employee=employee,
            start_location=start_location,
            end_location=end_location,
            start_time=trip_datetime,
            end_time=trip_datetime,
            transport_mode=transport_mode,
            distance_km=distance_km,
            carbon_savings=carbon_savings,
            credits_earned=credits_earned,
            notes=notes
        )
        
        # Create carbon credits
        if credits_earned > 0:
            CarbonCredit.objects.create(
                amount=credits_earned,
                source_trip=trip,
                owner_type='employee',
                owner_id=employee.id,
                status='pending',
                expiry_date=timezone.now() + timedelta(days=365)  # 1 year validity
            )
        
        messages.success(request, "Trip recorded successfully!")
        return redirect('employee_trips')
        
    except Exception as e:
        messages.error(request, f"An error occurred while recording the trip: {str(e)}")
        return redirect('employee_trip_log')

# For GET requests, redirect to the trip_log page
# return redirect('employee_trip_log') 