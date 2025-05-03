from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.contrib import messages
from users.models import CustomUser, EmployerProfile, EmployeeProfile, Location
from trips.models import Trip, CarbonCredit
from django.utils import timezone
import csv
import io
from django.urls import reverse
from decimal import Decimal
import json
from datetime import timedelta

# Import marketplace models if needed
from marketplace.models import MarketOffer, MarketplaceTransaction

def is_super_admin(user):
    return user.is_authenticated and user.is_super_admin

@login_required
@user_passes_test(is_super_admin)
def dashboard(request):
    """
    Admin dashboard view - shows system statistics
    """
    # Count total users, trips, and carbon credits
    total_users = CustomUser.objects.count()
    employers = EmployerProfile.objects.count()
    employees = EmployeeProfile.objects.count()
    bank_admins = CustomUser.objects.filter(is_bank_admin=True).count()
    super_admins = CustomUser.objects.filter(is_super_admin=True).count()
    pending_approval = EmployerProfile.objects.filter(approved=False).count()
    
    # Get from the trip and carbon credit models
    total_trips = Trip.objects.count()
    
    # Count new users in last 30 days
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    new_user_count = CustomUser.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Count recent trips in last 7 days
    seven_days_ago = timezone.now() - timezone.timedelta(days=7)
    recent_trip_count = Trip.objects.filter(trip_date__gte=seven_days_ago.date()).count()
    
    # Get carbon credits with proper formatting
    total_credits_raw = CarbonCredit.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_credits = round(float(total_credits_raw), 2)
    
    # Get pending employers for approval
    pending_employers = EmployerProfile.objects.filter(approved=False).select_related('user').order_by('-created_at')[:5]
    
    # Get recent trips for the dashboard
    recent_trips = Trip.objects.select_related(
        'employee', 'employee__user', 'employee__employer', 'start_location', 'end_location'
    ).order_by('-trip_date')[:10]
    
    # Get data for user growth chart (last 6 months)
    now = timezone.now()
    user_growth_data = []
    user_growth_labels = []
    
    for i in range(5, -1, -1):
        # Calculate month date
        current_date = now - timezone.timedelta(days=30 * i)
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
            month_end = next_month - timezone.timedelta(seconds=1)
        
        # Get users joined this month
        month_users = CustomUser.objects.filter(
            date_joined__gte=month_start,
            date_joined__lte=month_end
        ).count()
        
        # Add to data array
        user_growth_data.append(month_users)
        user_growth_labels.append(month_start.strftime('%b %Y'))
    
    # Get transport mode distribution data
    transport_modes = Trip.objects.values('transport_mode').annotate(
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
        'total_users': total_users,
        'employers': employers,
        'employees': employees,
        'employee_count': employees,
        'employer_count': employers,
        'bank_admin_count': bank_admins,
        'super_admin_count': super_admins,
        'pending_approval': pending_approval,
        'pending_approval_count': pending_approval,
        'total_trips': total_trips,
        'trip_count': total_trips,
        'recent_trip_count': recent_trip_count,
        'new_user_count': new_user_count,
        'total_credits': total_credits,
        'pending_employers': pending_employers,
        'recent_trips': recent_trips,
        'user_growth_data': json.dumps(user_growth_data),
        'user_growth_labels': json.dumps(user_growth_labels),
        'transport_mode_data': json.dumps(transport_mode_data),
        'transport_mode_labels': json.dumps(transport_mode_labels)
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_super_admin)
def dashboard_recent_trips(request):
    """
    HTMX-compatible view that returns recent trips for the admin dashboard
    """
    # Get recent trips with employee and location details
    trips = Trip.objects.select_related(
        'employee', 'employee__user', 'start_location', 'end_location'
    ).order_by('-trip_date')[:10]
    
    # Get transport modes for display
    transport_modes = Trip.TRANSPORT_MODES
    
    context = {
        'trips': trips,
        'transport_modes': transport_modes,
    }
    
    return render(request, 'admin/partials/recent_trips.html', context)

@login_required
@user_passes_test(is_super_admin)
def users_list(request):
    """Placeholder function for users list view"""
    return render(request, 'admin/users.html', {'users': []})

@login_required
@user_passes_test(is_super_admin)
def create_user(request):
    """Placeholder function for create user view"""
    return render(request, 'admin/create_user.html', {})

@login_required
@user_passes_test(is_super_admin)
def user_detail(request, user_id):
    """Placeholder function for user detail view"""
    user = get_object_or_404(CustomUser, id=user_id)
    trips = Trip.objects.filter(employee=user.employee_profile).order_by('-trip_date')[:10]
    context = {'user_detail': user, 'trips': trips}
    return render(request, 'admin/user_detail.html', context)

@login_required
@user_passes_test(is_super_admin)
def approve_user(request, user_id):
    """Placeholder function for approve user view"""
    return redirect('admin_users')

@login_required
@user_passes_test(is_super_admin)
def reject_user(request, user_id):
    """Placeholder function for reject user view"""
    return redirect('admin_users')

@login_required
@user_passes_test(is_super_admin)
def user_hierarchy(request):
    """Placeholder function for user hierarchy view"""
    return render(request, 'admin/user_hierarchy.html', {})

@login_required
@user_passes_test(is_super_admin)
def employers_list(request):
    """Placeholder function for employers list view"""
    return render(request, 'admin/employers.html', {'employers': []})

@login_required
@user_passes_test(is_super_admin)
def reports(request):
    """
    Admin reports view that handles different report types
    """
    report_type = request.GET.get('type', 'summary')
    date_range = request.GET.get('date_range', 'all')
    
    # Calculate date range
    end_date = timezone.now()
    if date_range == 'today':
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_range == 'week':
        start_date = end_date - timezone.timedelta(days=7)
    elif date_range == 'month':
        start_date = end_date - timezone.timedelta(days=30)
    elif date_range == 'year':
        start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # 'all'
        start_date = None
    
    # Base context
    context = {
        'report_type': report_type,
        'date_range': date_range,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    # Filter queryset based on date range if specified
    trips_qs = Trip.objects.all()
    credits_qs = CarbonCredit.objects.all()
    if start_date:
        trips_qs = trips_qs.filter(trip_date__gte=start_date.date(), trip_date__lte=end_date.date())
        credits_qs = credits_qs.filter(created_at__gte=start_date, created_at__lte=end_date)
    
    if report_type == 'summary':
        # User statistics
        context.update({
            'total_users': CustomUser.objects.count(),
            'total_employees': EmployeeProfile.objects.count(),
            'total_employers': EmployerProfile.objects.count(),
            
            # Trip statistics
            'total_trips': trips_qs.count(),
            'total_carbon_saved': trips_qs.aggregate(Sum('carbon_savings'))['carbon_savings__sum'] or 0,
            'avg_trips_per_user': round(trips_qs.count() / EmployeeProfile.objects.count(), 2) if EmployeeProfile.objects.count() > 0 else 0,
            
            # Credit statistics
            'total_credits': credits_qs.aggregate(Sum('amount'))['amount__sum'] or 0,
            'redeemed_credits': credits_qs.filter(status='redeemed').aggregate(Sum('amount'))['amount__sum'] or 0,
            'available_credits': (credits_qs.aggregate(Sum('amount'))['amount__sum'] or 0) - 
                               (credits_qs.filter(status='redeemed').aggregate(Sum('amount'))['amount__sum'] or 0),
            'avg_credits_per_trip': round((credits_qs.aggregate(Sum('amount'))['amount__sum'] or 0) / trips_qs.count(), 2) if trips_qs.count() > 0 else 0,
        })
    
    elif report_type == 'trips':
        # Calculate trip statistics
        total_distance = trips_qs.aggregate(Sum('distance'))['distance__sum'] or 0
        context.update({
            'total_trips': trips_qs.count(),
            'total_distance': total_distance,
            'total_carbon_saved': trips_qs.aggregate(Sum('carbon_savings'))['carbon_savings__sum'] or 0,
            'avg_trip_length': round(total_distance / trips_qs.count(), 1) if trips_qs.count() > 0 else 0,
            'trips': trips_qs.select_related('employee', 'employee__user').order_by('-trip_date')[:50],
            
            # Data for charts
            'trip_dates': list(trips_qs.dates('trip_date', 'day', order='ASC').values_list('trip_date', flat=True)),
            'trip_counts': list(trips_qs.values('trip_date').annotate(count=Count('id')).values_list('count', flat=True)),
            'transport_modes': list(dict(Trip.TRANSPORT_MODES).values()),
            'mode_counts': list(trips_qs.values('transport_mode').annotate(count=Count('id')).values_list('count', flat=True)),
        })
    
    elif report_type == 'credits':
        # Calculate credit statistics
        total_credits = credits_qs.aggregate(Sum('amount'))['amount__sum'] or 0
        context.update({
            'total_credits': total_credits,
            'redeemed_credits': credits_qs.filter(status='redeemed').aggregate(Sum('amount'))['amount__sum'] or 0,
            'pending_credits': credits_qs.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0,
            'avg_credits_per_user': round(total_credits / CustomUser.objects.count(), 2) if CustomUser.objects.count() > 0 else 0,
            'credits': credits_qs.select_related('user').order_by('-created_at')[:50],
            
            # Data for charts
            'credit_dates': list(credits_qs.dates('created_at', 'day', order='ASC').values_list('created_at__date', flat=True)),
            'credit_amounts': list(credits_qs.values('created_at__date').annotate(total=Sum('amount')).values_list('total', flat=True)),
        })
    
    elif report_type == 'users':
        # Calculate user statistics
        active_users = CustomUser.objects.filter(last_login__gte=timezone.now() - timezone.timedelta(days=30)).count()
        context.update({
            'total_users': CustomUser.objects.count(),
            'active_users': active_users,
            'inactive_users': CustomUser.objects.count() - active_users,
            'new_users': CustomUser.objects.filter(date_joined__gte=timezone.now() - timezone.timedelta(days=30)).count(),
            'users': CustomUser.objects.select_related('employee_profile', 'employer_profile').order_by('-date_joined')[:50],
            
            # Data for charts
            'user_dates': list(CustomUser.objects.dates('date_joined', 'day', order='ASC').values_list('date_joined__date', flat=True)),
            'user_counts': list(CustomUser.objects.values('date_joined__date').annotate(count=Count('id')).values_list('count', flat=True)),
        })
    
    return render(request, 'admin/reports.html', context)

@login_required
@user_passes_test(is_super_admin)
def export_reports(request):
    """Placeholder function for export reports view"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report.csv"'
    writer = csv.writer(response)
    writer.writerow(['No data'])
    return response

@login_required
@user_passes_test(is_super_admin)
def admin_profile(request):
    """Placeholder function for admin profile view"""
    return render(request, 'admin/profile.html', {'user': request.user})

@login_required
@user_passes_test(is_super_admin)
def admin_update_profile(request):
    """Placeholder function for admin update profile view"""
    return redirect('admin_profile')

@login_required
@user_passes_test(is_super_admin)
def admin_change_password(request):
    """Placeholder function for admin change password view"""
    return redirect('admin_profile')

@login_required
@user_passes_test(lambda u: u.is_super_admin or u.is_bank_admin)
def employer_approval(request, employer_id):
    """Placeholder function for employer approval view"""
    return redirect('admin_pending_employers')

@login_required
@user_passes_test(is_super_admin)
def generate_report(request):
    """Generate a report based on the specified parameters."""
    report_type = request.GET.get('type', 'all')
    date_range = request.GET.get('range', 'all')
    
    # Get base queryset
    trips = Trip.objects.all().select_related('employee', 'employee__user').order_by('-trip_date')
    
    # Apply date filters
    if date_range == 'week':
        trips = trips.filter(trip_date__gte=timezone.now().date() - timezone.timedelta(days=7))
    elif date_range == 'month':
        trips = trips.filter(trip_date__gte=timezone.now().date() - timezone.timedelta(days=30))
    elif date_range == 'quarter':
        trips = trips.filter(trip_date__gte=timezone.now().date() - timezone.timedelta(days=90))
    
    # Format trip data
    trip_data = []
    for trip in trips[:50]:  # Limit to 50 trips
        trip_data.append({
            'id': trip.id,
            'employee': trip.employee.user.get_full_name(),
            'date': trip.trip_date.strftime('%Y-%m-%d'),
            'transport_mode': trip.get_transport_mode_display(),
            'distance': trip.distance_km,
            'carbon_saved': trip.carbon_savings,
            'credits': trip.credits_earned,
            'status': trip.verification_status
        })
    
    return JsonResponse({'trips': trip_data})

@login_required
@user_passes_test(is_super_admin)
def export_report(request):
    """Export trip data to CSV."""
    # Get base queryset
    trips = Trip.objects.all().select_related('employee', 'employee__user').order_by('-trip_date')
    
    # Apply date filter if provided
    start_date = request.GET.get('start_date')
    if start_date:
        trips = trips.filter(trip_date__gte=start_date)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="trips_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Trip ID', 'Employee', 'Date', 'Transport Mode',
        'Distance (km)', 'Carbon Saved (kg)', 'Credits Earned',
        'Status'
    ])
    
    for trip in trips:
        writer.writerow([
            trip.id,
            trip.employee.user.get_full_name(),
            trip.trip_date.strftime('%Y-%m-%d'),
            trip.get_transport_mode_display(),
            trip.distance_km,
            trip.carbon_savings,
            trip.credits_earned,
            trip.verification_status
        ])
    
    return response

@login_required
@user_passes_test(is_super_admin)
def analytics(request):
    """
    Admin analytics view - shows comprehensive charts and statistics
    """
    # Date range for data (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get total carbon credits issued this month
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_carbon_credits = CarbonCredit.objects.filter(
        created_at__gte=month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get average trip distance
    avg_trip_distance = Trip.objects.aggregate(avg_distance=Sum('distance') / Count('id'))['avg_distance'] or 0
    
    # Get number of active employers
    active_employers = EmployerProfile.objects.filter(approved=True).count()
    
    # Get total carbon reduction
    carbon_reduction = Trip.objects.aggregate(Sum('carbon_savings'))['carbon_savings__sum'] or 0
    
    # Get total trips
    total_trips = Trip.objects.count()
    
    # Calculate change in trips compared to previous period
    prev_period_start = start_date - timedelta(days=days)
    current_period_trips = Trip.objects.filter(trip_date__gte=start_date).count()
    prev_period_trips = Trip.objects.filter(trip_date__gte=prev_period_start, trip_date__lt=start_date).count()
    trip_change = round(((current_period_trips - prev_period_trips) / max(prev_period_trips, 1)) * 100)
    
    # Get active users
    active_users = CustomUser.objects.filter(last_login__gte=start_date).count()
    prev_period_active = CustomUser.objects.filter(last_login__gte=prev_period_start, last_login__lt=start_date).count()
    user_change = round(((active_users - prev_period_active) / max(prev_period_active, 1)) * 100)
    
    # Calculate average credits per trip
    avg_credits_per_trip = round((total_carbon_credits / max(current_period_trips, 1)), 2)
    prev_avg_credits = CarbonCredit.objects.filter(
        created_at__gte=prev_period_start, created_at__lt=start_date
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    prev_avg_credits_per_trip = round((prev_avg_credits / max(prev_period_trips, 1)), 2)
    credits_change = round(((avg_credits_per_trip - prev_avg_credits_per_trip) / max(prev_avg_credits_per_trip, 1)) * 100)
    
    # Get data for credits over time chart
    credits_by_day = (
        CarbonCredit.objects
        .filter(created_at__gte=start_date)
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
        .filter(trip_date__gte=start_date)
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
        'active_employers': active_employers,
        'carbon_reduction': carbon_reduction,
        'total_trips': total_trips,
        'trip_change': trip_change,
        'active_users': active_users,
        'user_change': user_change,
        'avg_credits_per_trip': avg_credits_per_trip,
        'credits_change': credits_change,
        'dates': json.dumps(dates),
        'credits_data': json.dumps(credits_data),
        'transport_labels': json.dumps(transport_mode_labels),
        'transport_data': json.dumps(transport_mode_data),
    }
    
    return render(request, 'admin/analytics.html', context)

# Add additional admin views as needed 