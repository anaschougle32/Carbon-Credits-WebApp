from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Avg
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal
from users.models import Location
from .trips_views import create_trip

@login_required
@user_passes_test(lambda u: u.is_employee)
def dashboard(request):
    """
    Dashboard view for employee users.
    """
    context = {
        'page_title': 'Employee Dashboard',
    }
    
    return render(request, 'employee/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def trip_log(request):
    """
    View for logging new trips.
    """
    # Get employee profile
    employee = request.user.employee_profile
    
    # Check if this is a home location registration request
    if request.method == 'POST' and request.POST.get('register_home') == 'true':
        return register_home_location(request)
    
    # If POST request for a trip, handle form submission
    if request.method == 'POST':
        return create_trip(request)
    
    # For GET requests, render the form
    # Get employee's home location if it exists
    home_location = Location.objects.filter(
        created_by=request.user,
        location_type='home'
    ).first()
    
    has_home_location = home_location is not None
    
    # Get employer's locations
    employer_locations = []
    if employee.employer:
        employer_locations = employee.employer.office_locations.all()
    
    # Get today's date for the form
    today = timezone.now()
    
    context = {
        'page_title': 'Log a Trip',
        'employer_locations': employer_locations,
        'today': today,
        'has_home_location': has_home_location,
        'home_location': home_location,
    }
    
    return render(request, 'employee/trip_log.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def register_home_location(request):
    """
    Handle home location registration for employees.
    """
    if request.method == 'POST':
        try:
            # Get form data
            home_latitude = request.POST.get('home_latitude')
            home_longitude = request.POST.get('home_longitude')
            home_address = request.POST.get('home_address')
            
            # Validate required fields
            if not home_latitude or not home_longitude or not home_address:
                messages.error(request, "Please provide complete home location information.")
                return redirect('employee_trip_log')
            
            # Check if employee already has a home location
            existing_home = Location.objects.filter(
                created_by=request.user,
                location_type='home'
            ).first()
            
            if existing_home:
                # Update existing home location
                existing_home.latitude = Decimal(home_latitude)
                existing_home.longitude = Decimal(home_longitude)
                existing_home.address = home_address
                existing_home.save()
                messages.success(request, "Home location updated successfully.")
            else:
                # Create new home location
                Location.objects.create(
                    created_by=request.user,
                    name="Home",
                    latitude=Decimal(home_latitude),
                    longitude=Decimal(home_longitude),
                    address=home_address,
                    location_type='home',
                    is_primary=True,
                    employee=request.user.employee_profile
                )
                messages.success(request, "Home location registered successfully.")
            
            return redirect('employee_trip_log')
            
        except Exception as e:
            messages.error(request, f"Error registering home location: {str(e)}")
            return redirect('employee_trip_log')
    
    # For GET requests, redirect to trip log
    return redirect('employee_trip_log')

@login_required
@user_passes_test(lambda u: u.is_employee)
def trips_list(request):
    """
    View for listing all trips by the employee.
    """
    # Get employee profile
    employee = request.user.employee_profile
    
    # Get trips for this employee
    trips = employee.trips.all().order_by('-start_time')
    
    # Calculate aggregate statistics
    stats = trips.aggregate(
        total_distance=Sum('distance_km'),
        total_co2_saved=Sum('carbon_savings'),
        total_credits=Sum('credits_earned')
    )
    
    # Default values if no trips exist
    total_distance = stats['total_distance'] or 0
    total_co2_saved = stats['total_co2_saved'] or 0
    total_credits = stats['total_credits'] or 0
    
    context = {
        'trips': trips,
        'page_title': 'My Trips',
        'total_distance': total_distance,
        'total_co2_saved': total_co2_saved,
        'total_credits': total_credits,
    }
    
    return render(request, 'employee/trips.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def manage_home_location(request):
    """
    View for managing employee's home location.
    """
    # Get employee profile
    employee = request.user.employee_profile
    
    # Check if this is a POST request for updating home location
    if request.method == 'POST':
        try:
            # Get form data
            home_latitude = request.POST.get('home_latitude')
            home_longitude = request.POST.get('home_longitude')
            home_address = request.POST.get('home_address')
            home_name = request.POST.get('home_name', 'My Home')
            
            # Validate required fields
            if not home_latitude or not home_longitude or not home_address:
                messages.error(request, "Please provide complete home location information.")
                return redirect('employee_manage_home_location')
            
            # Check if employee already has a home location
            existing_home = Location.objects.filter(
                created_by=request.user,
                location_type='home'
            ).first()
            
            if existing_home:
                # Update existing home location
                existing_home.latitude = Decimal(home_latitude)
                existing_home.longitude = Decimal(home_longitude)
                existing_home.address = home_address
                existing_home.name = home_name
                existing_home.save()
                messages.success(request, "Home location updated successfully.")
            else:
                # Create new home location
                Location.objects.create(
                    created_by=request.user,
                    name=home_name,
                    latitude=Decimal(home_latitude),
                    longitude=Decimal(home_longitude),
                    address=home_address,
                    location_type='home',
                    is_primary=True,
                    employee=request.user.employee_profile
                )
                messages.success(request, "Home location registered successfully.")
            
            return redirect('employee_dashboard')
            
        except Exception as e:
            messages.error(request, f"Error saving home location: {str(e)}")
            return redirect('employee_manage_home_location')
    
    # For GET requests, show the form with existing data
    # Check if employee has a home location
    home_location = Location.objects.filter(
        created_by=request.user,
        location_type='home'
    ).first()
    
    has_home_location = home_location is not None
    
    context = {
        'page_title': 'Manage Home Location',
        'home_location': home_location,
        'has_home_location': has_home_location,
    }
    
    return render(request, 'employee/manage_home_location.html', context) 