from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Sum
from users.models import CustomUser, EmployerProfile, EmployeeProfile
from trips.models import Trip, CarbonCredit

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
    pending_approval = EmployerProfile.objects.filter(approved=False).count()
    
    # Get from the trip and carbon credit models
    total_trips = Trip.objects.count()
    total_credits = CarbonCredit.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get pending employers for approval
    pending_employers = EmployerProfile.objects.filter(approved=False).select_related('user').order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'employers': employers,
        'employees': employees,
        'pending_approval': pending_approval,
        'total_trips': total_trips,
        'total_credits': total_credits,
        'pending_employers': pending_employers,
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
    """
    Admin users management view
    """
    users = CustomUser.objects.all().order_by('-date_joined')
    
    context = {
        'users': users,
    }
    
    return render(request, 'admin/users.html', context)

@login_required
@user_passes_test(is_super_admin)
def reports(request):
    """
    Admin reports view
    """
    report_type = request.GET.get('type', 'summary')
    date_range = request.GET.get('date_range', 'all')
    
    # Base context
    context = {
        'report_type': report_type,
        'date_range': date_range,
    }
    
    # Additional data for summary report
    if report_type == 'summary':
        # User statistics
        total_users = CustomUser.objects.count()
        total_employees = EmployeeProfile.objects.count()
        total_employers = EmployerProfile.objects.count()
        
        # Trip statistics
        total_trips = Trip.objects.count()
        total_carbon_saved = Trip.objects.aggregate(Sum('carbon_savings'))['carbon_savings__sum'] or 0
        
        # Calculate average trips per employee
        avg_trips_per_user = 0
        if total_employees > 0:
            avg_trips_per_user = total_trips / total_employees
            
        # Credit statistics
        total_credits = CarbonCredit.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        redeemed_credits = CarbonCredit.objects.filter(status='redeemed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Add stats to context
        context.update({
            'total_users': total_users,
            'total_employees': total_employees,
            'total_employers': total_employers,
            'total_trips': total_trips,
            'total_carbon_saved': total_carbon_saved,
            'avg_trips_per_user': round(avg_trips_per_user, 2),
            'total_credits': total_credits,
            'redeemed_credits': redeemed_credits,
        })
    
    return render(request, 'admin/reports.html', context) 