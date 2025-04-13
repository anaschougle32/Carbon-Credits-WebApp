from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
@user_passes_test(lambda u: u.is_employer)
def dashboard(request):
    """
    Dashboard view for employer users.
    """
    context = {
        'page_title': 'Employer Dashboard',
    }
    
    return render(request, 'employer/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_employer)
def employees_list(request):
    """
    View for listing and managing employees.
    """
    # Get employees for this employer
    employees = request.user.employer_profile.employees.all()
    
    context = {
        'employees': employees,
        'page_title': 'Manage Employees',
    }
    
    return render(request, 'employer/employees.html', context)

@login_required
@user_passes_test(lambda u: u.is_employer)
def locations_list(request):
    """
    View for listing and managing office locations.
    """
    # Get locations for this employer
    locations = request.user.employer_profile.locations.all()
    
    context = {
        'locations': locations,
        'page_title': 'Manage Locations',
    }
    
    return render(request, 'employer/locations.html', context)

@login_required
@user_passes_test(lambda u: u.is_employer)
def trading(request):
    """
    View for carbon credit trading.
    """
    context = {
        'page_title': 'Carbon Credit Trading',
    }
    
    return render(request, 'employer/trading.html', context) 