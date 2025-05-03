from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.contrib import messages
from users.models import CustomUser, EmployeeProfile, EmployerProfile, Location
from trips.models import Trip, CarbonCredit
from marketplace.models import MarketOffer, MarketplaceTransaction
from django.core.paginator import Paginator
import json
from datetime import timedelta
from core.models import Reward, RewardRedemption

def is_employee(user):
    return user.is_authenticated and user.is_employee

@login_required
@user_passes_test(is_employee)
def dashboard(request):
    """
    Employee dashboard view
    """
    employee = request.user.employee_profile
    
    # Get trip statistics
    all_trips = Trip.objects.filter(employee=employee)
    total_trips = all_trips.count()
    completed_trips = all_trips.filter(verification_status='verified').count()
    
    # Calculate total distance traveled and CO2 saved
    co2_saved = all_trips.filter(verification_status='verified').aggregate(Sum('carbon_savings'))['carbon_savings__sum'] or 0
    total_credits = all_trips.filter(verification_status='verified').aggregate(Sum('credits_earned'))['credits_earned__sum'] or 0
    
    # Get recent trips
    recent_trips = all_trips.order_by('-trip_date', '-created_at')[:5]
    
    # Get data for credits over time chart (last 6 months)
    now = timezone.now()
    credits_data = []
    credits_labels = []
    
    for i in range(5, -1, -1):
        # Calculate month date
        current_date = now - timedelta(days=30 * i)
        month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # If it's the current month, use current date as end date
        if i == 0:
            month_end = now
        else:
            # Otherwise, get the last day of the month
            if month_start.month == 12:
                next_month = month_start.replace(year=month_start.year + 1, month=1)
            else:
                next_month = month_start.replace(month=month_start.month + 1)
            month_end = next_month - timedelta(seconds=1)
        
        # Get credits for this month
        month_credits = all_trips.filter(
            trip_date__gte=month_start,
            trip_date__lte=month_end,
            verification_status='verified'
        ).aggregate(total=Sum('credits_earned'))['total'] or 0
        
        # Add to data array
        credits_data.append(float(month_credits))
        credits_labels.append(month_start.strftime('%b %Y'))
    
    # Get transport mode distribution data
    transport_modes = all_trips.values('transport_mode').annotate(
        count=Count('id')
    ).order_by('-count')
    
    transport_mode_labels = []
    transport_mode_data = []
    
    mode_names = dict(Trip.TRANSPORT_MODES)
    for mode in transport_modes:
        transport_mode_labels.append(mode_names.get(mode['transport_mode'], 'Unknown'))
        transport_mode_data.append(mode['count'])
    
    context = {
        'title': 'Employee Dashboard',
        'employee': employee,
        'total_trips': total_trips,
        'completed_trips': completed_trips,
        'co2_saved': co2_saved,
        'total_credits': total_credits,
        'recent_trips': recent_trips,
        'credits_data': json.dumps(credits_data),
        'credits_labels': json.dumps(credits_labels),
        'transport_mode_labels': json.dumps(transport_mode_labels),
        'transport_mode_data': json.dumps(transport_mode_data)
    }
    
    return render(request, 'employee/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def credits_list(request):
    """View for displaying employee's credit history and balance."""
    employee = request.user.employee_profile
    
    # Get all trips and their credits
    trips = Trip.objects.filter(employee=employee).order_by('-trip_date')
    
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

@login_required
@user_passes_test(is_employee)
def analytics(request):
    """
    Employee analytics view - shows personal statistics and charts
    """
    employee = request.user.employee_profile
    
    # Date range for data (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get employee's trip data
    trips = Trip.objects.filter(employee=employee)
    
    # Get total carbon credits earned by this employee
    total_carbon_credits = CarbonCredit.objects.filter(
        trip__employee=employee, 
        created_at__gte=start_date
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get average trip distance
    avg_trip_distance = trips.aggregate(Avg('distance'))['distance__avg'] or 0
    
    # Get total carbon reduction
    carbon_reduction = trips.aggregate(Sum('carbon_savings'))['carbon_savings__sum'] or 0
    
    # Get total trips
    total_trips = trips.filter(trip_date__gte=start_date).count()
    
    # Calculate change in trips compared to previous period
    prev_period_start = start_date - timedelta(days=days)
    current_period_trips = trips.filter(trip_date__gte=start_date).count()
    prev_period_trips = trips.filter(trip_date__gte=prev_period_start, trip_date__lt=start_date).count()
    trip_change = round(((current_period_trips - prev_period_trips) / max(prev_period_trips, 1)) * 100)
    
    # Calculate average credits per trip
    avg_credits_per_trip = round((total_carbon_credits / max(current_period_trips, 1)), 2)
    prev_avg_credits = CarbonCredit.objects.filter(
        trip__employee=employee,
        created_at__gte=prev_period_start, 
        created_at__lt=start_date
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    prev_avg_credits_per_trip = round((prev_avg_credits / max(prev_period_trips, 1)), 2)
    credits_change = round(((avg_credits_per_trip - prev_avg_credits_per_trip) / max(prev_avg_credits_per_trip, 1)) * 100)
    
    # Get data for credits over time chart
    credits_by_day = (
        CarbonCredit.objects
        .filter(trip__employee=employee, created_at__gte=start_date)
        .extra(select={'day': "DATE(created_at)"})
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )
    
    # If no data, create sample data
    dates = []
    credits_data = []
    
    if credits_by_day:
        for entry in credits_by_day:
            dates.append(entry['day'].strftime('%Y-%m-%d'))
            credits_data.append(float(entry['total']))
    else:
        # Generate sample data
        for i in range(days):
            current_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            dates.append(current_date)
            credits_data.append(round(float(i % 5) + 0.5 + (i % 3), 2))
    
    # Get data for transport mode distribution chart
    transport_modes = (
        Trip.objects
        .filter(employee=employee, trip_date__gte=start_date)
        .values('transport_mode')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # If no transport data, create sample data
    transport_mode_labels = []
    transport_mode_data = []
    
    if transport_modes:
        mode_dict = dict(Trip.TRANSPORT_MODES)
        for mode in transport_modes:
            transport_mode_labels.append(mode_dict.get(mode['transport_mode'], mode['transport_mode']))
            transport_mode_data.append(mode['count'])
    else:
        transport_mode_labels = ['Bicycle', 'Public Transport', 'Walking', 'Work From Home', 'Carpool']
        transport_mode_data = [12, 8, 6, 5, 3]
    
    context = {
        'total_carbon_credits': total_carbon_credits,
        'avg_trip_distance': avg_trip_distance,
        'carbon_reduction': carbon_reduction,
        'total_trips': total_trips,
        'trip_change': trip_change,
        'avg_credits_per_trip': avg_credits_per_trip,
        'credits_change': credits_change,
        'dates': json.dumps(dates),
        'credits_data': json.dumps(credits_data),
        'transport_labels': json.dumps(transport_mode_labels),
        'transport_data': json.dumps(transport_mode_data),
        'employee': employee,
    }
    
    return render(request, 'employee/analytics.html', context) 