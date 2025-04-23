from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from decimal import Decimal
import uuid

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
        start_location_id = request.POST.get('start_location')
        end_location_id = request.POST.get('end_location')
        transport_mode = request.POST.get('transport_mode')
        trip_date_str = request.POST.get('trip_date')
        
        # Validate required fields
        if not all([start_location_id, end_location_id, transport_mode, trip_date_str]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('employee_trip_log')
        
        # Get employee profile
        employee = request.user.employee_profile
        
        # Handle custom locations (marked as 'other' in dropdown)
        start_location = None
        end_location = None
        distance_km = None
        
        # Process start location
        if start_location_id == 'home':
            # Use employee's home location
            start_location = Location.objects.filter(
                created_by=request.user,
                location_type='home'
            ).first()
            
            if not start_location:
                messages.error(request, "Home location not found. Please set your home location first.")
                return redirect('employee_trip_log')
        elif start_location_id == 'other':
            # Create a custom location for this trip
            lat = request.POST.get('custom_latitude')
            lng = request.POST.get('custom_longitude')
            address = request.POST.get('custom_address', 'Custom location')
            
            if not lat or not lng:
                messages.error(request, "Custom location coordinates are required.")
                return redirect('employee_trip_log')
            
            # Create a temporary location (not saved to database)
            start_location = Location(
                name=f"Custom Start {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                latitude=Decimal(lat),
                longitude=Decimal(lng),
                address=address,
                location_type='custom',
                created_by=request.user
            )
            start_location.save()
        else:
            # Use an existing location from database
            try:
                start_location = Location.objects.get(id=start_location_id)
            except Location.DoesNotExist:
                messages.error(request, "Selected start location does not exist.")
                return redirect('employee_trip_log')
        
        # Process end location
        if end_location_id == 'home':
            # Use employee's home location
            end_location = Location.objects.filter(
                created_by=request.user,
                location_type='home'
            ).first()
            
            if not end_location:
                messages.error(request, "Home location not found. Please set your home location first.")
                return redirect('employee_trip_log')
        elif end_location_id == 'other':
            # Create a custom location for this trip
            lat = request.POST.get('custom_latitude')
            lng = request.POST.get('custom_longitude')
            address = request.POST.get('custom_address', 'Custom location')
            
            if not lat or not lng:
                messages.error(request, "Custom location coordinates are required.")
                return redirect('employee_trip_log')
            
            # Create a temporary location (not saved to database)
            end_location = Location(
                name=f"Custom End {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                latitude=Decimal(lat),
                longitude=Decimal(lng),
                address=address,
                location_type='custom',
                created_by=request.user
            )
            end_location.save()
        else:
            # Use an existing location from database
            try:
                end_location = Location.objects.get(id=end_location_id)
            except Location.DoesNotExist:
                messages.error(request, "Selected end location does not exist.")
                return redirect('employee_trip_log')
        
        # Get distance
        # distance_km = request.POST.get('distance_km')
        distance_km = get_distance(
            (start_location.latitude, start_location.longitude),
            (end_location.latitude, end_location.longitude),
        )

        if not distance_km and transport_mode != 'work_from_home':
            messages.error(request, "Trip distance is required.")
            return redirect('employee_trip_log')
        
        # For work from home, set distance to 0
        if transport_mode == 'work_from_home':
            distance_km = 0
        
        # Create the trip with start time only (this means trip is in progress)
        distance_decimal = Decimal(distance_km) if distance_km else Decimal('0')
        
        # Parse trip date
        trip_date = datetime.strptime(trip_date_str, "%Y-%m-%d").date()
        
        # Set trip time to current time, but with the selected date
        trip_start = timezone.now().replace(
            year=trip_date.year,
            month=trip_date.month,
            day=trip_date.day
        )
        
        # For completed trips, set end time 30 minutes later
        trip_end = trip_start + timezone.timedelta(minutes=30)
        
        # Create the trip
        trip = Trip(
            employee=employee,
            start_location=start_location,
            end_location=end_location,
            start_time=trip_start,
            end_time=trip_end,
            transport_mode=transport_mode,
            distance_km=distance_decimal,
            # status='completed'
        )
        
        # Calculate carbon savings based on transport mode and distance
        carbon_savings = 0
        
        if transport_mode == 'work_from_home':
            # Fixed carbon savings for WFH
            carbon_savings = 10
        else:
            # Calculate based on mode and distance
            mode_factors = {
                'walking': 6,
                'bicycle': 5,
                'public_transport': 3,
                'carpool': 2,
                'car': 0.5
            }
            factor = mode_factors.get(transport_mode, 1)
            carbon_savings = float(distance_decimal) * factor
        
        # Save carbon savings as Decimal
        trip.carbon_savings = Decimal(str(carbon_savings))
        trip.credits_earned = Decimal(str(carbon_savings))
        
        # Handle trip proof
        proof_image = request.FILES.get('proof_image')
        proof_data = request.POST.get('proof_image')
        
        if proof_image:
            # Handle traditional file upload
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.{proof_image.name.split('.')[-1]}"
            
            # Save the proof image
            trip.proof_image = proof_image
            trip.verification_status = 'pending'
        elif proof_data and proof_data.startswith('data:'):
            # Handle base64 data from the enhanced file upload component
            import base64
            from django.core.files.base import ContentFile
            
            # Extract the data type and base64 content
            format, imgstr = proof_data.split(';base64,')
            ext = format.split('/')[-1]
            
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.{ext}"
            
            # Convert base64 to file and save
            data = ContentFile(base64.b64decode(imgstr), name=filename)
            trip.proof_image = data
            trip.verification_status = 'pending'
        else:
            # All trips require employer approval
            trip.verification_status = 'pending'
        
        # Save the trip
        trip.save()
        
        # Create carbon credits
        if trip.verification_status == 'verified':
            # Create active credits for verified trips
            CarbonCredit.objects.create(
                amount=trip.credits_earned,
                source_trip=trip,
                owner_type='employee',
                owner_id=employee.id,
                status='active',
                expiry_date=timezone.now() + timezone.timedelta(days=365)
            )
        else:
            # Create pending credits for trips needing verification
            CarbonCredit.objects.create(
                amount=trip.credits_earned,
                source_trip=trip,
                owner_type='employee',
                owner_id=employee.id,
                status='pending',
                expiry_date=timezone.now() + timezone.timedelta(days=365)
            )
        
        messages.success(
            request, 
            f"Trip logged successfully! You've earned {trip.credits_earned} carbon credits."
        )
        return redirect('employee_dashboard')
        
    except Exception as e:
        messages.error(request, f"Error creating trip: {str(e)}")
        return redirect('employee_trip_log')

# For GET requests, redirect to the trip_log page
# return redirect('employee_trip_log') 