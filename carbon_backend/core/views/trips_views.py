from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from decimal import Decimal

from users.models import CustomUser, EmployeeProfile, Location
from trips.models import Trip

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

@login_required
@user_passes_test(lambda u: u.is_employee)
def create_trip(request):
    """
    Handle the creation of a new trip.
    """
    if request.method == 'POST':
        try:
            # Get employee profile
            employee = request.user.employee_profile
            
            # Get basic trip info
            transport_mode = request.POST.get('transport_mode')
            trip_date_str = request.POST.get('trip_date')
            
            # Validate required fields
            if not transport_mode or not trip_date_str:
                messages.error(request, "Please fill in all required fields.")
                return redirect('employee_trip_log')
            
            # Convert trip date string to datetime
            trip_date = datetime.strptime(trip_date_str, '%Y-%m-%d').date()
            start_time = timezone.make_aware(datetime.combine(trip_date, datetime.min.time()))
            
            # Work from home is a special case
            if transport_mode == 'work_from_home':
                with transaction.atomic():
                    # Create a trip without start/end locations
                    trip = Trip.objects.create(
                        employee=employee,
                        start_time=start_time,
                        end_time=start_time,  # Same as start time for WFH
                        transport_mode=transport_mode,
                        distance_km=Decimal('0'),  # No distance for WFH
                        carbon_savings=CO2_SAVINGS[transport_mode],
                        credits_earned=CREDIT_RATES[transport_mode],
                        verification_status='verified',  # Auto-verify WFH
                        duration_minutes=0  # No travel time for WFH
                    )
                    
                    messages.success(request, f"Work from home logged successfully! You earned {CREDIT_RATES[transport_mode]} carbon credits.")
                    return redirect('employee_trips')
            
            # Process locations
            start_location_id = request.POST.get('start_location')
            end_location_id = request.POST.get('end_location')
            
            start_location = None
            end_location = None
            
            # Process start location
            if start_location_id == 'home':
                # Get employee's home location
                try:
                    start_location = Location.objects.filter(
                        created_by=request.user,
                        location_type='home'
                    ).first()
                    if not start_location:
                        messages.error(request, "No home location found. Please set your home location in your profile.")
                        return redirect('employee_trip_log')
                except Exception as e:
                    messages.error(request, f"Error finding home location: {str(e)}")
                    return redirect('employee_trip_log')
            elif start_location_id == 'other':
                # Create a custom location
                try:
                    latitude = request.POST.get('custom_latitude')
                    longitude = request.POST.get('custom_longitude')
                    address = request.POST.get('custom_address')
                    
                    if not latitude or not longitude or not address:
                        messages.error(request, "Please provide complete location information.")
                        return redirect('employee_trip_log')
                    
                    start_location = Location.objects.create(
                        created_by=request.user,
                        name=f"Trip Start - {trip_date_str}",
                        latitude=Decimal(latitude),
                        longitude=Decimal(longitude),
                        address=address,
                        location_type='commute'
                    )
                except Exception as e:
                    messages.error(request, f"Error creating custom location: {str(e)}")
                    return redirect('employee_trip_log')
            else:
                # Get existing location
                try:
                    start_location = Location.objects.get(id=start_location_id)
                except Location.DoesNotExist:
                    messages.error(request, "Invalid start location selected.")
                    return redirect('employee_trip_log')
            
            # Process end location (similar to start location)
            if end_location_id == 'home':
                try:
                    end_location = Location.objects.filter(
                        created_by=request.user,
                        location_type='home'
                    ).first()
                    if not end_location:
                        messages.error(request, "No home location found. Please set your home location in your profile.")
                        return redirect('employee_trip_log')
                except Exception as e:
                    messages.error(request, f"Error finding home location: {str(e)}")
                    return redirect('employee_trip_log')
            elif end_location_id == 'other':
                try:
                    # Check if we have office coordinates from the form
                    office_lat = request.POST.get('office_latitude')
                    office_lng = request.POST.get('office_longitude')
                    office_address = request.POST.get('office_address')
                    
                    if office_lat and office_lng and office_address:
                        # Use office coordinates from the form
                        latitude = office_lat
                        longitude = office_lng
                        address = office_address
                    else:
                        # Fall back to custom coordinates
                        latitude = request.POST.get('custom_latitude')
                        longitude = request.POST.get('custom_longitude')
                        address = request.POST.get('custom_address')
                    
                    if not latitude or not longitude or not address:
                        messages.error(request, "Please provide complete location information.")
                        return redirect('employee_trip_log')
                    
                    end_location = Location.objects.create(
                        created_by=request.user,
                        name=f"Trip End - {trip_date_str}",
                        latitude=Decimal(latitude),
                        longitude=Decimal(longitude),
                        address=address,
                        location_type='commute'
                    )
                except Exception as e:
                    messages.error(request, f"Error creating custom location: {str(e)}")
                    return redirect('employee_trip_log')
            else:
                try:
                    end_location = Location.objects.get(id=end_location_id)
                except Location.DoesNotExist:
                    messages.error(request, "Invalid end location selected.")
                    return redirect('employee_trip_log')
            
            # Get distance from form (calculated by JavaScript)
            distance_str = request.POST.get('distance_km', '0')
            try:
                distance_km = Decimal(distance_str)
            except:
                distance_km = Decimal('0')
            
            # Calculate carbon savings and credits earned
            carbon_savings = distance_km * CO2_SAVINGS[transport_mode]
            credits_earned = distance_km * CREDIT_RATES[transport_mode]
            
            # Calculate travel time based on transport mode and distance
            speed_kmh = TRANSPORT_SPEEDS.get(transport_mode, 30)  # Default to 30 km/h if mode not found
            
            # Calculate duration in minutes (speed in km/h, distance in km)
            if speed_kmh > 0:
                duration_minutes = int((distance_km / speed_kmh) * 60)
            else:
                duration_minutes = 0
            
            # Calculate end time based on duration
            end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes > 0 else start_time
            
            # Handle proof image if provided
            proof_image = request.FILES.get('proof_image')
            
            # Create the trip
            with transaction.atomic():
                trip = Trip.objects.create(
                    employee=employee,
                    start_location=start_location,
                    end_location=end_location,
                    start_time=start_time,
                    end_time=end_time,
                    transport_mode=transport_mode,
                    distance_km=distance_km,
                    carbon_savings=carbon_savings,
                    credits_earned=credits_earned,
                    proof_image=proof_image,
                    duration_minutes=duration_minutes,
                    verification_status='pending'
                )
                
                messages.success(request, f"Trip logged successfully! You've earned {credits_earned} carbon credits (pending verification).")
                return redirect('employee_trips')
                
        except Exception as e:
            messages.error(request, f"Error creating trip: {str(e)}")
            return redirect('employee_trip_log')
    
    # For GET requests, redirect to the trip_log page
    return redirect('employee_trip_log') 