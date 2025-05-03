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
from datetime import timedelta, datetime

def is_employer(user):
    return user.is_authenticated and user.is_employer

@login_required
@user_passes_test(is_employer)
def dashboard(request):
    """
    Employer dashboard view
    """
    # Get the employer profile
    employer_profile = request.user.employer_profile
    
    # Basic statistics
    total_employees = EmployeeProfile.objects.filter(employer=employer_profile).count()
    active_employees = EmployeeProfile.objects.filter(
        employer=employer_profile, 
        user__is_active=True,
        user__last_login__gte=(timezone.now() - timedelta(days=30))
    ).count()
    
    # Employee IDs for filtering
    employee_ids = EmployeeProfile.objects.filter(employer=employer_profile).values_list('id', flat=True)
    
    # Trip statistics
    all_trips = Trip.objects.filter(employee__employer=employer_profile)
    total_trips = all_trips.count()
    pending_trips = all_trips.filter(verification_status='pending').count()
    
    # Carbon savings
    co2_saved = all_trips.aggregate(total=Sum('carbon_savings'))['total'] or 0
    
    # Calculate tree equivalent (rough approximation - 1 tree absorbs ~22kg CO2/year)
    tree_equivalent = round(co2_saved / 22)
    
    # Get pending trips for approval section
    pending_approval_trips = all_trips.filter(
        verification_status='pending'
    ).select_related('employee', 'employee__user', 'start_location', 'end_location').order_by('-trip_date')[:5]
    
    # Carbon credit statistics
    total_credits = all_trips.aggregate(total=Sum('credits_earned'))['total'] or 0
    
    # Calculate credits growth (this month vs last month)
    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = this_month_start - timedelta(seconds=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    this_month_credits = all_trips.filter(
        trip_date__gte=this_month_start
    ).aggregate(total=Sum('credits_earned'))['total'] or 0
    
    last_month_credits = all_trips.filter(
        trip_date__gte=last_month_start,
        trip_date__lt=this_month_start
    ).aggregate(total=Sum('credits_earned'))['total'] or 0
    
    # Prevent division by zero
    if last_month_credits > 0:
        credits_growth = ((this_month_credits - last_month_credits) / last_month_credits) * 100
    else:
        credits_growth = 100 if this_month_credits > 0 else 0
    
    # Get top employees data
    top_employees = EmployeeProfile.objects.filter(
        employer=employer_profile
    ).annotate(
        trips_count=Count('trips'),
        total_credits=Sum('trips__credits_earned'),
        co2_saved=Sum('trips__carbon_savings')
    ).order_by('-trips_count')[:5]

    # Get data for monthly credits chart (last 6 months)
    monthly_credits_data = []
    monthly_labels = []
    
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
            trip_date__lte=month_end
        ).aggregate(total=Sum('credits_earned'))['total'] or 0
        
        # Add to data array
        monthly_credits_data.append(float(month_credits))
        monthly_labels.append(month_start.strftime('%b %Y'))
    
    # Check if we have any data, if not, add sample data
    if sum(monthly_credits_data) == 0:
        monthly_credits_data = [2.5, 4.2, 3.8, 5.1, 6.3, 7.2]  # Sample data
    
    # Get transport mode distribution data
    transport_modes = all_trips.values('transport_mode').annotate(
        count=Count('id')
    ).order_by('-count')
    
    transport_mode_labels = []
    transport_mode_data = []
    
    # Handle case of no data
    if not transport_modes:
        transport_mode_labels = ['Public Transport', 'Carpool', 'Personal Vehicle']
        transport_mode_data = [5, 3, 2]  # Sample data
    else:
        mode_names = dict(Trip.TRANSPORT_MODES)
        for mode in transport_modes:
            transport_mode_labels.append(mode_names.get(mode['transport_mode'], 'Unknown'))
            transport_mode_data.append(mode['count'])
    
    context = {
        'title': 'Employer Dashboard',
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_trips': total_trips,
        'pending_trips': pending_trips,
        'total_credits': total_credits,
        'credits_growth': credits_growth,
        'co2_saved': co2_saved,
        'tree_equivalent': tree_equivalent,
        'top_employees': top_employees,
        'pending_approval_trips': pending_approval_trips,
        'monthly_credits': json.dumps(monthly_credits_data),
        'monthly_labels': json.dumps(monthly_labels),
        'transport_mode_labels': json.dumps(transport_mode_labels),
        'transport_mode_data': json.dumps(transport_mode_data)
    }
    
    return render(request, 'employer/dashboard.html', context)

@login_required
@user_passes_test(is_employer)
def analytics(request):
    """
    Employer analytics view - shows comprehensive charts and statistics about employees
    """
    employer = request.user.employer_profile
    
    # Date range for data (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get employee count
    total_employees = EmployeeProfile.objects.filter(employer=employer).count()
    
    # Get total carbon credits for this employer
    total_carbon_credits = CarbonCredit.objects.filter(
        trip__employee__employer=employer, 
        created_at__gte=start_date
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get average trip distance for this employer's employees
    trips = Trip.objects.filter(employee__employer=employer)
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
    
    # Get active employees
    active_employees = EmployeeProfile.objects.filter(
        employer=employer,
        user__last_login__gte=start_date
    ).count()
    prev_period_active = EmployeeProfile.objects.filter(
        employer=employer,
        user__last_login__gte=prev_period_start, 
        user__last_login__lt=start_date
    ).count()
    employee_change = round(((active_employees - prev_period_active) / max(prev_period_active, 1)) * 100)
    
    # Calculate average credits per trip
    avg_credits_per_trip = round((total_carbon_credits / max(current_period_trips, 1)), 2)
    prev_avg_credits = CarbonCredit.objects.filter(
        trip__employee__employer=employer,
        created_at__gte=prev_period_start, 
        created_at__lt=start_date
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    prev_avg_credits_per_trip = round((prev_avg_credits / max(prev_period_trips, 1)), 2)
    credits_change = round(((avg_credits_per_trip - prev_avg_credits_per_trip) / max(prev_avg_credits_per_trip, 1)) * 100)
    
    # Get data for credits over time chart
    credits_by_day = (
        CarbonCredit.objects
        .filter(trip__employee__employer=employer, created_at__gte=start_date)
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
        .filter(employee__employer=employer, trip_date__gte=start_date)
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
        'active_employees': active_employees,
        'carbon_reduction': carbon_reduction,
        'total_trips': total_trips,
        'trip_change': trip_change,
        'total_employees': total_employees,
        'employee_change': employee_change,
        'avg_credits_per_trip': avg_credits_per_trip,
        'credits_change': credits_change,
        'dates': json.dumps(dates),
        'credits_data': json.dumps(credits_data),
        'transport_labels': json.dumps(transport_mode_labels),
        'transport_data': json.dumps(transport_mode_data),
    }
    
    return render(request, 'employer/analytics.html', context) 