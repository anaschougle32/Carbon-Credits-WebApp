from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from .models import CustomUser, EmployerProfile, EmployeeProfile, Location
from .serializers import (
    UserSerializer,
    EmployerProfileSerializer,
    EmployeeProfileSerializer,
    LocationSerializer,
    EmployerRegistrationSerializer,
    EmployeeRegistrationSerializer,
)
# Import permissions
from .permissions import IsEmployer, IsBankAdmin, IsSuperAdmin, IsEmployee, IsOwnerOrAdmin, IsApprovedUser
from django.contrib import messages
from django.contrib.auth import login
from .forms import EmployeeRegistrationForm
import decimal


class CurrentUserView(APIView):
    """View to get the current authenticated user's details."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class RegisterView(generics.CreateAPIView):
    """View to register a new user."""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer
    template_name = None
    
    def get(self, request, *args, **kwargs):
        """Handle GET request - display the registration options page."""
        return render(request, self.template_name)


class EmployerRegistrationView(APIView):
    """View to register a new employer."""
    
    permission_classes = [permissions.AllowAny]
    template_name = 'registration/register_employer.html'
    
    def get(self, request):
        """Handle GET request - display the registration form."""
        serializer = EmployerRegistrationSerializer()
        # Initialize an empty errors dict to avoid template errors
        serializer._errors = {}
        return render(request, self.template_name, {
            'serializer': serializer,
            'page_title': 'Employer Registration',
            'page_description': 'Register your company to manage employee carbon credits'
        })
    
    def post(self, request):
        """Handle POST request - process the registration form."""
        serializer = EmployerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                # Get validated data
                email = serializer.validated_data.get('email')
                password = serializer.validated_data.get('password')
                company_name = serializer.validated_data.get('company_name')
                
                # Create user with automatic approval
                user = CustomUser.objects.create_user(
                    username=email,  # Use email as username
                    email=email,
                    password=password,
                    is_employer=True,
                    is_staff=True,
                    is_active=True,
                    approved=True  # Automatically approve employer
                )
                
                # Create employer profile with automatic approval
                employer_profile = EmployerProfile.objects.create(
                    user=user,
                    company_name=company_name,
                    approved=True  # Automatically approve employer profile
                )
                
                # Log the user in
                login(request, user)
                
                if request.accepts('text/html'):
                    messages.success(request, 'Registration successful! Welcome to the Carbon Credits platform.')
                    return redirect('employer:employer_dashboard')
                
                return Response(
                    {
                        "detail": "Employer registration successful.",
                        "user_id": user.id
                    },
                    status=status.HTTP_201_CREATED
                )
        
        if request.accepts('text/html'):
            return render(request, self.template_name, {
                'serializer': serializer,
                'page_title': 'Employer Registration',
                'page_description': 'Register your company to manage employee carbon credits'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeRegistrationView(APIView):
    """View to register a new employee."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Handle GET request - display the registration form."""
        form = EmployeeRegistrationForm()
        return render(request, 'auth/register_employee.html', {'form': form})
    
    def post(self, request):
        """Handle POST request - process the registration form."""
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Get form data
                email = form.cleaned_data['email']
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                employer = form.cleaned_data['employer']
                employee_id = form.cleaned_data['employee_id']
                home_address = form.cleaned_data['home_address']
                
                # Check if user already exists
                existing_user = CustomUser.objects.filter(email=email).first()
                if existing_user:
                    # If the user exists but has no employee profile, they might be registering as an employee
                    if hasattr(existing_user, 'employee_profile'):
                        # User is already registered as an employee
                        form.add_error('email', 'A user with this email is already registered as an employee.')
                        return render(request, 'auth/register_employee.html', {'form': form})
                    
                    # If user is an employer or admin, they can't register as an employee
                    if existing_user.is_employer or existing_user.is_bank_admin or existing_user.is_super_admin:
                        form.add_error('email', 'This email is already registered as an employer or administrator.')
                        return render(request, 'auth/register_employee.html', {'form': form})
                    
                    # For other cases (e.g., user exists but no role), we update the user instead of creating a new one
                    user = existing_user
                    user.first_name = first_name
                    user.last_name = last_name
                    user.is_employee = True
                    user.approved = False
                    user.save()
                    
                    # If they provided a new password, update it
                    if password:
                        user.set_password(password)
                        user.save()
                else:
                    # Create new user (inactive until approved)
                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        is_employee=True,
                        is_active=True,  # User can login but cannot access restricted areas
                        approved=False  # User is not fully approved
                    )
                
                # Check if employee profile already exists
                employee_profile = EmployeeProfile.objects.filter(user=user).first()
                if not employee_profile:
                    # Create employee profile (pending approval)
                    employee_profile = EmployeeProfile.objects.create(
                        user=user,
                        employer=employer,
                        employee_id=employee_id,
                        approved=False  # Needs employer approval
                    )
                else:
                    # Update existing employee profile
                    employee_profile.employer = employer
                    employee_profile.employee_id = employee_id
                    employee_profile.approved = False
                    employee_profile.save()
                
                # Create home location
                Location.objects.create(
                    created_by=user,
                    name="Home",
                    latitude=decimal.Decimal('0.0'),
                    longitude=decimal.Decimal('0.0'),
                    address=home_address,
                    location_type='home',
                    is_primary=True
                )
                
                # Set registration type and redirect to pending approval page
                request.session['registration_type'] = 'employee'
                messages.success(request, "Registration successful! Your account is pending approval from your employer.")
                return redirect('pending_approval')
        
        return render(request, 'auth/register_employee.html', {'form': form})


class EmployerListView(generics.ListAPIView):
    """View to list all employers."""
    
    permission_classes = [IsBankAdmin]
    queryset = EmployerProfile.objects.all()
    serializer_class = EmployerProfileSerializer


class EmployerDetailView(generics.RetrieveUpdateAPIView):
    """View to get and update employer details."""
    
    permission_classes = [IsOwnerOrAdmin]
    queryset = EmployerProfile.objects.all()
    serializer_class = EmployerProfileSerializer


class EmployerApprovalView(APIView):
    """View to approve/reject an employer."""
    
    permission_classes = [IsBankAdmin]
    
    def patch(self, request, pk):
        employer_profile = get_object_or_404(EmployerProfile, pk=pk)
        
        # Get approval status from request data
        approved = request.data.get('approved', None)
        if approved is None:
            return Response(
                {"detail": "Approval status required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update user approval status
        with transaction.atomic():
            user = employer_profile.user
            user.approved = approved
            user.save()
            
            # Update profile approval status
            employer_profile.approved = approved
            employer_profile.save()
        
        return Response(
            {"detail": f"Employer {'approved' if approved else 'rejected'} successfully"},
            status=status.HTTP_200_OK
        )


class EmployeeListView(generics.ListAPIView):
    """View to list employees (filtered by employer)."""
    
    permission_classes = [IsEmployer | IsBankAdmin]
    serializer_class = EmployeeProfileSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Bank admins and super admins can see all employees
        if user.is_super_admin or user.is_bank_admin:
            return EmployeeProfile.objects.all()
            
        # Employers can see their employees
        if hasattr(user, 'employer_profile'):
            return EmployeeProfile.objects.filter(employer=user.employer_profile)
            
        return EmployeeProfile.objects.none()


class EmployeeDetailView(generics.RetrieveUpdateAPIView):
    """View to get and update employee details."""
    
    permission_classes = [IsOwnerOrAdmin]
    serializer_class = EmployeeProfileSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Bank admins and super admins can see all employees
        if user.is_super_admin or user.is_bank_admin:
            return EmployeeProfile.objects.all()
            
        # Employers can see their employees
        if hasattr(user, 'employer_profile'):
            return EmployeeProfile.objects.filter(employer=user.employer_profile)
            
        # Employees can see themselves
        if hasattr(user, 'employee_profile'):
            return EmployeeProfile.objects.filter(pk=user.employee_profile.pk)
            
        return EmployeeProfile.objects.none()


class EmployeeApprovalView(APIView):
    """View to approve/reject an employee."""
    
    permission_classes = [IsEmployer]
    
    def patch(self, request, pk):
        # Get the employee profile
        employee_profile = get_object_or_404(EmployeeProfile, pk=pk)
        
        # Check if the employee belongs to the employer
        if hasattr(request.user, 'employer_profile'):
            if employee_profile.employer != request.user.employer_profile:
                return Response(
                    {"detail": "This employee does not belong to your company"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Get approval status from request data
        approved = request.data.get('approved', None)
        if approved is None:
            return Response(
                {"detail": "Approval status required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update user approval status
        with transaction.atomic():
            user = employee_profile.user
            user.approved = approved
            user.save()
            
            # Update profile approval status
            employee_profile.approved = approved
            employee_profile.save()
        
        return Response(
            {"detail": f"Employee {'approved' if approved else 'rejected'} successfully"},
            status=status.HTTP_200_OK
        )


class LocationListCreateView(generics.ListCreateAPIView):
    """View to list and create locations."""
    
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]
    serializer_class = LocationSerializer
    
    def get_queryset(self):
        # Filter locations based on user role
        user = self.request.user
        
        if user.is_super_admin or user.is_bank_admin:
            # Admins can see all locations
            return Location.objects.all()
        elif user.is_employer:
            # Employers can see their office locations
            return Location.objects.filter(employer=user.employer_profile)
        elif user.is_employee:
            # Employees can see their home location and employer's office locations
            return Location.objects.filter(
                created_by=user
            ) | Location.objects.filter(
                employer=user.employee_profile.employer
            )
        
        return Location.objects.none()
    
    def perform_create(self, serializer):
        # If the user is an employer, set the employer field
        if hasattr(self.request.user, 'employer_profile'):
            serializer.save(created_by=self.request.user, employer=self.request.user.employer_profile)
        else:
            serializer.save(created_by=self.request.user)


class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View to retrieve, update or delete a location."""
    
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser, IsOwnerOrAdmin]
    serializer_class = LocationSerializer
    
    def get_queryset(self):
        # Filter locations based on user role (same as above)
        user = self.request.user
        
        if user.is_super_admin or user.is_bank_admin:
            return Location.objects.all()
        elif user.is_employer:
            return Location.objects.filter(employer=user.employer_profile)
        elif user.is_employee:
            return Location.objects.filter(
                created_by=user
            ) | Location.objects.filter(
                employer=user.employee_profile.employer
            )
        
        return Location.objects.none()


class PendingApprovalView(APIView):
    """View for displaying the pending approval page."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        return render(request, 'registration/pending_approval.html')
