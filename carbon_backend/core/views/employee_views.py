from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

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
    context = {
        'page_title': 'Log a Trip',
    }
    
    return render(request, 'employee/trip_log.html', context)

@login_required
@user_passes_test(lambda u: u.is_employee)
def trips_list(request):
    """
    View for listing all trips by the employee.
    """
    # Get trips for this employee
    trips = request.user.employee_profile.trips.all().order_by('-start_time')
    
    context = {
        'trips': trips,
        'page_title': 'My Trips',
    }
    
    return render(request, 'employee/trips.html', context) 