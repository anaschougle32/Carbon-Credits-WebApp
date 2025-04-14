from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.contrib import messages
from users.models import CustomUser, EmployerProfile, EmployeeProfile, Location
from trips.models import Trip, CarbonCredit
from django.utils import timezone

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
    Admin users management view with enhanced filtering and search
    """
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'date_joined')
    sort_dir = request.GET.get('dir', 'desc')
    
    # Start with all users
    users_queryset = CustomUser.objects.all()
    
    # Apply role filter
    if role_filter:
        if role_filter == 'super_admin':
            users_queryset = users_queryset.filter(is_super_admin=True)
        elif role_filter == 'bank_admin':
            users_queryset = users_queryset.filter(is_bank_admin=True)
        elif role_filter == 'employer':
            users_queryset = users_queryset.filter(is_employer=True)
        elif role_filter == 'employee':
            users_queryset = users_queryset.filter(is_employee=True)
    
    # Apply status filter
    if status_filter:
        if status_filter == 'approved':
            users_queryset = users_queryset.filter(approved=True)
        elif status_filter == 'pending':
            users_queryset = users_queryset.filter(approved=False)
    
    # Apply search filter
    if search_query:
        users_queryset = users_queryset.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(employer_profile__company_name__icontains=search_query)
        ).distinct()
    
    # Apply sorting
    if sort_by == 'name':
        order_field = 'first_name' if sort_dir == 'asc' else '-first_name'
    elif sort_by == 'email':
        order_field = 'email' if sort_dir == 'asc' else '-email'
    elif sort_by == 'role':
        # Sorting by role is complex - fallback to date joined
        order_field = '-date_joined'
    else:  # default to date_joined
        order_field = 'date_joined' if sort_dir == 'asc' else '-date_joined'
    
    users_queryset = users_queryset.order_by(order_field)
    
    # Prefetch related profiles for optimization
    users_queryset = users_queryset.prefetch_related(
        'employer_profile', 
        'employee_profile', 
        'employee_profile__employer'
    )
    
    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(users_queryset, 20)  # 20 users per page
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'sort_by': sort_by,
        'sort_dir': sort_dir,
        'page_obj': users,
        'total_users': users_queryset.count(),
    }
    
    return render(request, 'admin/users.html', context)

@login_required
@user_passes_test(is_super_admin)
def user_detail(request, user_id):
    """
    Detailed view for a specific user
    """
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Get user's profile based on role
    profile = None
    if user.is_employer:
        profile = getattr(user, 'employer_profile', None)
    elif user.is_employee:
        profile = getattr(user, 'employee_profile', None)
    
    # Get user's trips if they're an employee
    trips = []
    if user.is_employee and hasattr(user, 'employee_profile'):
        trips = Trip.objects.filter(employee=user.employee_profile).order_by('-start_time')[:10]
    
    # Get user's locations
    locations = Location.objects.filter(created_by=user)
    
    # Get carbon credits for this user
    credits = None
    if user.is_employee and hasattr(user, 'employee_profile'):
        credits = CarbonCredit.objects.filter(owner_type='employee', owner_id=user.employee_profile.id)
    
    context = {
        'user_detail': user,
        'profile': profile,
        'trips': trips,
        'locations': locations,
        'credits': credits,
    }
    
    return render(request, 'admin/user_detail.html', context)

@login_required
@user_passes_test(is_super_admin)
def approve_user(request, user_id):
    """
    Approve a user account
    """
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")
    
    user = get_object_or_404(CustomUser, id=user_id)
    user.approved = True
    user.save()
    
    # Also approve profile if exists
    if user.is_employer and hasattr(user, 'employer_profile'):
        user.employer_profile.approved = True
        user.employer_profile.save()
    elif user.is_employee and hasattr(user, 'employee_profile'):
        user.employee_profile.approved = True
        user.employee_profile.save()
    
    messages.success(request, f"User {user.email} has been approved.")
    
    # Return partial HTML for HTMX or redirect
    if request.headers.get('HX-Request'):
        return render(request, 'admin/partials/user_row.html', {'user': user})
    
    return redirect('admin_users')

@login_required
@user_passes_test(is_super_admin)
def reject_user(request, user_id):
    """
    Reject a user account
    """
    if request.method != 'POST':
        return HttpResponseForbidden("Method not allowed")
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Mark as rejected by setting approved to False
    user.approved = False
    user.save()
    
    # Also update profile if exists
    if user.is_employer and hasattr(user, 'employer_profile'):
        user.employer_profile.approved = False
        user.employer_profile.save()
    elif user.is_employee and hasattr(user, 'employee_profile'):
        user.employee_profile.approved = False
        user.employee_profile.save()
    
    messages.success(request, f"User {user.email} has been rejected.")
    
    # Return partial HTML for HTMX or redirect
    if request.headers.get('HX-Request'):
        return render(request, 'admin/partials/user_row.html', {'user': user})
    
    return redirect('admin_users')

@login_required
@user_passes_test(is_super_admin)
def user_hierarchy(request):
    """
    View for displaying user hierarchy
    """
    # Get all employers with their employees
    employers = EmployerProfile.objects.prefetch_related(
        'user', 
        'employees',
        'employees__user'
    ).order_by('company_name')
    
    # Get admins (super admins and bank admins)
    admins = CustomUser.objects.filter(
        Q(is_super_admin=True) | Q(is_bank_admin=True)
    ).order_by('email')
    
    context = {
        'employers': employers,
        'admins': admins,
    }
    
    return render(request, 'admin/user_hierarchy.html', context)

@login_required
@user_passes_test(is_super_admin)
def create_user(request):
    """
    Create a new user
    """
    if request.method == 'POST':
        # Extract form data
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        password = request.POST.get('password')
        
        # Basic validation
        if not all([email, role, password]):
            messages.error(request, "Please fill all required fields.")
            return redirect('admin_create_user')
        
        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, f"User with email {email} already exists.")
            return redirect('admin_create_user')
        
        # Create the user
        user = CustomUser.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            approved=True  # Auto-approve users created by admin
        )
        
        # Set role flags
        if role == 'super_admin':
            user.is_super_admin = True
            user.is_staff = True
            user.is_superuser = True
        elif role == 'bank_admin':
            user.is_bank_admin = True
            user.is_staff = True
        elif role == 'employer':
            user.is_employer = True
            # Create employer profile
            company_name = request.POST.get('company_name', '')
            registration_number = request.POST.get('registration_number', '')
            industry = request.POST.get('industry', '')
            
            if not all([company_name, registration_number]):
                messages.warning(request, f"User created but employer profile is incomplete.")
            else:
                EmployerProfile.objects.create(
                    user=user,
                    company_name=company_name,
                    registration_number=registration_number,
                    industry=industry,
                    approved=True
                )
        elif role == 'employee':
            user.is_employee = True
            # Would need employer ID to create employee profile
            employer_id = request.POST.get('employer_id')
            if employer_id:
                try:
                    employer = EmployerProfile.objects.get(id=employer_id)
                    EmployeeProfile.objects.create(
                        user=user,
                        employer=employer,
                        approved=True
                    )
                except EmployerProfile.DoesNotExist:
                    messages.warning(request, f"User created but employee profile could not be linked to employer.")
        
        user.save()
        messages.success(request, f"User {email} has been created successfully.")
        return redirect('admin_users')
    
    # GET request - show the create user form
    employers = EmployerProfile.objects.filter(approved=True).order_by('company_name')
    
    context = {
        'employers': employers,
    }
    
    return render(request, 'admin/create_user.html', context)

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