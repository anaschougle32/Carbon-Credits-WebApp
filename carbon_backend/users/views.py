from django.shortcuts import render, get_object_or_404
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


class EmployerRegistrationView(APIView):
    """View to register a new employer."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = EmployerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                # Create user
                user_data = serializer.validated_data.pop('user')
                password = user_data.pop('password')
                user = CustomUser.objects.create(**user_data, is_employer=True)
                user.set_password(password)
                user.save()
                
                # Create employer profile
                EmployerProfile.objects.create(user=user, **serializer.validated_data)
                
                # Return user data
                return Response(
                    {
                        "detail": "Employer registration successful. Awaiting approval.",
                        "redirect_url": "/registration/pending-approval/"
                    },
                    status=status.HTTP_201_CREATED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeRegistrationView(APIView):
    """View to register a new employee."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = EmployeeRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                # Create user
                user_data = serializer.validated_data.pop('user')
                password = user_data.pop('password')
                user = CustomUser.objects.create(**user_data, is_employee=True)
                user.set_password(password)
                user.save()
                
                # Create employee profile
                EmployeeProfile.objects.create(user=user, **serializer.validated_data)
                
                # Return user data
                return Response(
                    {
                        "detail": "Employee registration successful. Awaiting approval.",
                        "redirect_url": "/registration/pending-approval/"
                    },
                    status=status.HTTP_201_CREATED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
