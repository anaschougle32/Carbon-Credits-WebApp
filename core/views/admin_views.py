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
    recent_trip_count = Trip.objects.filter(start_time__gte=seven_days_ago).count()
    
    # Get carbon credits with proper formatting
    total_credits_raw = CarbonCredit.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_credits = round(float(total_credits_raw), 2)
    
    # Get pending employers for approval
    pending_employers = EmployerProfile.objects.filter(approved=False).select_related('user').order_by('-created_at')[:5]
    
    # Get recent trips for the dashboard
    recent_trips = Trip.objects.select_related(
        'employee', 'employee__user', 'employee__employer', 'start_location', 'end_location'
    ).order_by('-start_time')[:10]
    
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
    ).order_by('-start_time')[:10]
    
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
    return render(request, 'admin/user_detail.html', {'user_detail': None})

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
        trips_qs = trips_qs.filter(start_time__gte=start_date, start_time__lte=end_date)
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
            'trips': trips_qs.select_related('employee', 'employee__user').order_by('-start_time')[:50],
            
            # Data for charts
            'trip_dates': list(trips_qs.dates('start_time', 'day', order='ASC').values_list('start_time__date', flat=True)),
            'trip_counts': list(trips_qs.values('start_time__date').annotate(count=Count('id')).values_list('count', flat=True)),
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

# Add additional admin views as needed 