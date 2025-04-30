from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Avg
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal
from users.models import Location
from .trips_views import create_trip
from django.core.paginator import Paginator
from django.db.models import Q
from trips.models import CarbonCredit, Trip
from django.conf import settings
from users.models import CustomUser
from django.urls import reverse
from users.models import EmployeeProfile
from marketplace.models import MarketOffer, EmployeeCreditOffer
from datetime import timedelta
from django.db.models.functions import TruncMonth

@login_required
@user_passes_test(lambda u: u.is_employee)
def dashboard(request):
    """
    Dashboard view for employees.
    """
    employee = request.user.employee_profile
    
    # Get trip statistics
    total_trips = Trip.objects.filter(employee=employee).count()
    completed_trips = Trip.objects.filter(
        employee=employee, 
        verification_status='verified'
    ).count()
    
    # Calculate total distance traveled
    total_distance = Trip.objects.filter(
        employee=employee,
        verification_status='verified'
    ).aggregate(Sum('distance_km'))['distance_km__sum'] or 0
    
    # Calculate CO2 saved
    co2_saved = Trip.objects.filter(
        employee=employee,
        verification_status='verified'
    ).aggregate(Sum('carbon_savings'))['carbon_savings__sum'] or 0
    
    # Get recent trips
    recent_trips = Trip.objects.filter(
        employee=employee
    ).order_by('-start_time')[:5]
    
    # Get pending trips
    pending_trips = Trip.objects.filter(
        employee=employee,
        verification_status='pending'
    ).count()
    
    context = {
        'page_title': 'Employee Dashboard',
        'employee': employee,
        'total_trips': total_trips,
        'completed_trips': completed_trips,
        'total_distance': total_distance,
        'co2_saved': co2_saved,
        'recent_trips': recent_trips,
        'pending_trips': pending_trips,
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
        total_co2_saved=Sum('carbon_savings')
    )
    
    # Default values if no trips exist
    total_distance = stats['total_distance'] or 0
    total_co2_saved = stats['total_co2_saved'] or 0
    
    context = {
        'trips': trips,
        'page_title': 'My Trips',
        'total_distance': total_distance,
        'total_co2_saved': total_co2_saved,
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

@login_required
@user_passes_test(lambda u: u.is_employee)
def profile(request):
    """View for employee profile page."""
    # Get the employee profile and stats
    employee_profile = getattr(request.user, 'employee_profile', None)
    
    # Get home location
    home_location = Location.objects.filter(
        created_by=request.user,
        location_type='home'
    ).first()
    
    # Get employee stats
    stats = {
        'total_credits': 0,
        'redeemed_credits': 0,
        'available_credits': 0,
        'total_trips': 0,
        'co2_saved': 0
    }
    
    if employee_profile:
        # Get trips
        trips = Trip.objects.filter(employee=employee_profile)
        total_trips = trips.count()
        
        # Carbon credits
        total_credits = CarbonCredit.objects.filter(
            owner_type='employee',
            owner_id=employee_profile.id
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        redeemed_credits = CarbonCredit.objects.filter(
            owner_type='employee',
            owner_id=employee_profile.id,
            status='redeemed'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # CO2 saved
        co2_saved = trips.aggregate(Sum('carbon_savings'))['carbon_savings__sum'] or 0
        
        stats = {
            'total_credits': total_credits,
            'redeemed_credits': redeemed_credits,
            'available_credits': total_credits - redeemed_credits,
            'total_trips': total_trips,
            'co2_saved': co2_saved
        }
    
    # Maps API key for displaying maps
    google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
    
    context = {
        'page_title': 'Employee Profile',
        'user': request.user,
        'employee_profile': employee_profile,
        'home_location': home_location,
        'stats': stats,
        'google_maps_api_key': google_maps_api_key
    }
    return render(request, 'employee/profile.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def update_profile(request):
    """Handle employee profile updates."""
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        
        # Validate email format
        if not email or '@' not in email:
            messages.error(request, "Please provide a valid email address.")
            return redirect('employee_profile')
        
        # Check if email is already in use by another user
        if CustomUser.objects.exclude(id=request.user.id).filter(email=email).exists():
            messages.error(request, "This email is already in use by another user.")
            return redirect('employee_profile')
        
        # Update user data
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        messages.success(request, "Profile updated successfully.")
        return redirect('employee_profile')
    
    # For GET requests, redirect to profile page
    return redirect('employee_profile')

@login_required
@user_passes_test(lambda u: u.is_employee)
def update_home_location(request):
    """Handle updating home location."""
    if request.method == 'POST':
        # Get form data
        address = request.POST.get('address')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
        # Validate data
        if not address or not latitude or not longitude:
            messages.error(request, "Please provide complete location information.")
            return redirect('employee_profile')
        
        try:
            # Check if home location exists
            home_location = Location.objects.filter(
                created_by=request.user,
                location_type='home'
            ).first()
            
            if home_location:
                # Update existing location
                home_location.address = address
                home_location.latitude = Decimal(latitude)
                home_location.longitude = Decimal(longitude)
                home_location.save()
            else:
                # Create new home location
                home_location = Location.objects.create(
                    created_by=request.user,
                    name="Home",
                    address=address,
                    latitude=Decimal(latitude),
                    longitude=Decimal(longitude),
                    location_type='home',
                    is_primary=True,
                    employee=request.user.employee_profile
                )
            
            messages.success(request, "Home location updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating home location: {str(e)}")
        
        return redirect('employee_profile')
    
    # For GET requests, show a form to update home location
    # Get current home location
    home_location = Location.objects.filter(
        created_by=request.user,
        location_type='home'
    ).first()
    
    # Maps API key for displaying maps
    google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
    
    context = {
        'page_title': 'Update Home Location',
        'home_location': home_location,
        'google_maps_api_key': google_maps_api_key
    }
    return render(request, 'employee/update_home_location.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def change_password(request):
    """Handle employee password changes."""
    if request.method == 'POST':
        # Get form data
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate passwords
        if not current_password or not new_password or not confirm_password:
            messages.error(request, "Please fill in all password fields.")
            return redirect('employee_profile')
        
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect('employee_profile')
        
        # Check current password
        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect('employee_profile')
        
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        
        messages.success(request, "Password changed successfully.")
        return redirect('employee_profile')
    
    # For GET requests, redirect to profile page
    return redirect('employee_profile')

@login_required
@user_passes_test(lambda u: u.is_employee)
def marketplace(request):
    """
    View for employee marketplace to buy/sell credits to their employer.
    """
    employee = request.user.employee_profile
    employer = employee.employer
    
    # Get employee's active credits
    employee_credits = CarbonCredit.objects.filter(
        owner_type='employee',
        owner_id=employee.id,
        status='active'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get current market rate (average price from active market offers)
    market_rate = MarketOffer.objects.filter(
        status='active'
    ).aggregate(Avg('price_per_credit'))['price_per_credit__avg'] or 5.0  # Default to $5 if no data
    
    # Get pending offers
    pending_offers = EmployeeCreditOffer.objects.filter(
        employee=employee,
        status='pending'
    ).order_by('-created_at')
    
    # Get completed offers
    completed_offers = EmployeeCreditOffer.objects.filter(
        employee=employee,
        status__in=['approved', 'rejected', 'cancelled']
    ).order_by('-processed_at')[:10]  # Show last 10
    
    if request.method == 'POST':
        offer_type = request.POST.get('offer_type')
        credit_amount = request.POST.get('credit_amount')
        
        try:
            credit_amount = float(credit_amount)
            
            # Validate input
            if credit_amount <= 0:
                messages.error(request, "Credit amount must be positive")
                return redirect('employee_marketplace')
                
            # For selling: check if employee has enough credits
            if offer_type == 'sell' and credit_amount > employee_credits:
                messages.error(request, f"You don't have enough credits. Available: {employee_credits}")
                return redirect('employee_marketplace')
            
            # For buying: implement any validation if needed
            
            # Calculate total amount based on market rate
            total_amount = Decimal(str(credit_amount)) * Decimal(str(market_rate))
            
            # Create the offer
            EmployeeCreditOffer.objects.create(
                employee=employee,
                employer=employer,
                offer_type=offer_type,
                credit_amount=credit_amount,
                market_rate=market_rate,
                total_amount=total_amount,
                status='pending'
            )
            
            if offer_type == 'buy':
                messages.success(request, f"Your request to buy {credit_amount} credits for ${total_amount:.2f} has been submitted to your employer.")
            else:
                messages.success(request, f"Your request to sell {credit_amount} credits for ${total_amount:.2f} has been submitted to your employer.")
                
        except ValueError:
            messages.error(request, "Invalid credit amount")
        except Exception as e:
            messages.error(request, f"Error processing request: {str(e)}")
    
    context = {
        'page_title': 'Marketplace',
        'employee': employee,
        'employer': employer,
        'employee_credits': employee_credits,
        'market_rate': market_rate,
        'pending_offers': pending_offers,
        'completed_offers': completed_offers,
        'wallet_balance': employee.wallet_balance
    }
    
    return render(request, 'employee/marketplace.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def cancel_offer(request, offer_id):
    """
    Cancel a pending credit offer.
    """
    employee = request.user.employee_profile
    
    try:
        offer = get_object_or_404(
            EmployeeCreditOffer, 
            id=offer_id, 
            employee=employee,
            status='pending'
        )
        
        offer.status = 'cancelled'
        offer.processed_at = timezone.now()
        offer.save()
        
        messages.success(request, "Your offer has been cancelled.")
        
    except EmployeeCreditOffer.DoesNotExist:
        messages.error(request, "Offer not found or already processed.")
    
    return redirect('employee_marketplace')

@login_required
def credits_list(request):
    """Display employee's carbon credits and history."""
    employee = request.user.employee_profile
    
    # Get all credits for the employee
    credits = CarbonCredit.objects.filter(
        owner_type='employee',
        owner_id=employee.id
    ).order_by('-created_at')
    
    # Calculate total credits
    total_credits = credits.aggregate(total=Sum('amount'))['total'] or 0
    
    # Get credit history grouped by month
    credit_history = credits.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('-month')
    
    # Convert credit history to list for JSON serialization
    credit_history_list = [
        {
            'month': item['month'].strftime('%Y-%m-%d'),
            'total': float(item['total'])
        }
        for item in credit_history
    ]
    
    context = {
        'credits': credits,
        'total_credits': total_credits,
        'credit_history': credit_history_list,
    }
    
    return render(request, 'employee/credits.html', context) 