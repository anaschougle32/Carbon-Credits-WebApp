from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from users.models import CustomUser, EmployerProfile, EmployeeProfile, Location
from users.forms import LoginForm, EmployeeRegistrationForm

def login_view(request):
    if request.user.is_authenticated:
        # If authenticated, redirect to appropriate dashboard
        if request.user.is_employee:
            return redirect('employee_dashboard')
        elif request.user.is_employer:
            return redirect('employer_dashboard')
        else:
            return redirect('admin:index')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name()}!")
                
                if user.is_employee:
                    return redirect('employee_dashboard')
                elif user.is_employer:
                    return redirect('employer_dashboard')
                else:
                    return redirect('admin:index')
            else:
                messages.error(request, "Invalid email or password. Please try again.")
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')

def employee_register(request):
    """Handle employee registration."""
    # Create form instance
    form = EmployeeRegistrationForm()
    
    if request.method == 'POST':
        # Get form data
        form = EmployeeRegistrationForm(request.POST)
        
        if form.is_valid():
            # Get form data
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            employer = form.cleaned_data['employer']
            employee_id = form.cleaned_data['employee_id']
            home_address = form.cleaned_data['home_address']
            
            # Check if user with this email already exists
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, "A user with this email already exists.")
                return render(request, 'registration/register_employee.html', {'form': form})
            
            try:
                # Create user account (set approved to True)
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_employee=True,
                    is_active=True,
                    approved=True  # User is automatically approved
                )
                
                # Create employee profile
                employee_profile = EmployeeProfile.objects.create(
                    user=user,
                    employer=employer,
                    employee_id=employee_id,
                    approved=True  # Automatically approved
                )
                
                # Create home location (without coordinates)
                Location.objects.create(
                    user=user,
                    name="Home",
                    address=home_address,
                    location_type='home'
                )
                
                messages.success(request, "Registration successful! You can now log in.")
                return redirect('login')
                
            except Exception as e:
                messages.error(request, f"An error occurred during registration: {str(e)}")
    
    return render(request, 'registration/register_employee.html', {'form': form})

def employer_register(request):
    """Handle employer registration."""
    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Company information
        company_name = request.POST.get('company_name')
        industry = request.POST.get('industry')
        phone = request.POST.get('phone')
        website = request.POST.get('website', '')
        
        # Address information
        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2', '')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        country = request.POST.get('country')
        
        # Remove latitude and longitude checks
        
        # Validate required fields
        if not all([email, password, first_name, last_name, company_name, industry, phone,
                    address_line1, city, state, postal_code, country]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'registration/register_employer.html')
        
        # Check if user with this email already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, 'registration/register_employer.html')
        
        try:
            # Create user account
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_employer=True,
                is_active=True,
                approved=False  # Needs admin approval
            )
            
            # Format full address
            full_address = f"{address_line1}"
            if address_line2:
                full_address += f", {address_line2}"
            full_address += f", {city}, {state} {postal_code}, {country}"
            
            # Create employer profile
            employer_profile = EmployerProfile.objects.create(
                user=user,
                company_name=company_name,
                industry=industry,
                phone=phone,
                website=website,
                address=full_address,
                approved=False  # Needs admin approval
            )
            
            # Create primary office location without coordinates
            primary_location = Location.objects.create(
                user=user,
                employer=employer_profile,
                name=f"{company_name} Headquarters",
                address=full_address,
                location_type='office',
                is_primary=True
            )
            
            messages.success(request, "Registration successful! Your account is pending approval from the system administrator.")
            request.session['registration_type'] = 'employer'
            return redirect('pending_approval')
            
        except Exception as e:
            messages.error(request, f"An error occurred during registration: {str(e)}")
    
    return render(request, 'registration/register_employer.html') 