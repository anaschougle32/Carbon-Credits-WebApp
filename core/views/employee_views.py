from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from core.models import Trip, Reward, RewardRedemption, Location

def is_employee(user):
    return user.is_authenticated and user.is_employee

@login_required
@user_passes_test(is_employee)
def dashboard(request):
    """
    Employee dashboard view
    """
    context = {
        'title': 'Employee Dashboard'
    }
    return render(request, 'employee/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def credits_list(request):
    """View for displaying employee's credit history and balance."""
    employee = request.user.employee_profile
    
    # Get all trips and their credits
    trips = Trip.objects.filter(employee=employee).order_by('-start_time')
    
    # Calculate total credits
    total_credits = trips.aggregate(Sum('credits_earned'))['credits_earned__sum'] or 0
    
    # Calculate credits by category
    credits_by_category = trips.values('transport_mode').annotate(
        total_credits=Sum('credits_earned'),
        trip_count=Count('id')
    ).order_by('-total_credits')
    
    context = {
        'page_title': 'My Credits',
        'page_description': 'View your credit history and balance',
        'trips': trips,
        'total_credits': total_credits,
        'credits_by_category': credits_by_category,
    }
    
    return render(request, 'employee/credits.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def rewards_list(request):
    """View for displaying available rewards and redemption history."""
    employee = request.user.employee_profile
    
    # Get available rewards
    available_rewards = Reward.objects.filter(
        is_active=True,
        employer=employee.employer
    ).order_by('-credits_required')
    
    # Get redemption history
    redemption_history = RewardRedemption.objects.filter(
        employee=employee
    ).order_by('-redeemed_at')
    
    context = {
        'page_title': 'Rewards',
        'page_description': 'View and redeem your rewards',
        'available_rewards': available_rewards,
        'redemption_history': redemption_history,
        'current_credits': employee.wallet_balance,
    }
    
    return render(request, 'employee/rewards.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def settings(request):
    """View for managing employee settings."""
    employee = request.user.employee_profile
    
    # Get user's home location
    home_location = Location.objects.filter(
        created_by=request.user,
        location_type='home'
    ).first()
    
    context = {
        'page_title': 'Settings',
        'page_description': 'Manage your account settings',
        'employee': employee,
        'home_location': home_location,
    }
    
    return render(request, 'employee/settings.html', context) 