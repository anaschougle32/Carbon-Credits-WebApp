from django.db import models
from django.utils import timezone
from users.models import CustomUser, EmployeeProfile, Location
from decimal import Decimal


class Trip(models.Model):
    """Model for tracking employee trips."""
    
    TRANSPORT_MODES = (
        ('car', 'Car (Single Occupancy)'),
        ('carpool', 'Carpool'),
        ('public_transport', 'Public Transport'),
        ('bicycle', 'Bicycle'),
        ('walking', 'Walking'),
        ('work_from_home', 'Work From Home'),
    )
    
    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
    )
    
    employee = models.ForeignKey(
        EmployeeProfile, 
        on_delete=models.CASCADE, 
        related_name='trips'
    )
    start_location = models.ForeignKey(
        Location, 
        on_delete=models.SET_NULL, 
        related_name='trip_starts',
        null=True
    )
    end_location = models.ForeignKey(
        Location, 
        on_delete=models.SET_NULL, 
        related_name='trip_ends',
        null=True
    )
    trip_date = models.DateField(default=timezone.now)
    start_time = models.TimeField(default=timezone.now)
    end_time = models.TimeField(default=timezone.now)
    transport_mode = models.CharField(
        max_length=20, 
        choices=TRANSPORT_MODES
    )
    distance_km = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True,
        blank=True
    )
    carbon_savings = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True,
        blank=True
    )
    credits_earned = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    verification_status = models.CharField(
        max_length=10,
        choices=VERIFICATION_STATUS,
        default='pending'
    )
    verified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='verified_trips',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.employee.user.email}: {self.trip_date} ({self.transport_mode})"
    
    def calculate_credits(self):
        """Calculate carbon credits based on transport mode and distance."""
        if self.transport_mode == 'work_from_home':
            return Decimal('10')  # Fixed credits for WFH
            
        mode_factors = {
            'walking': Decimal('6'),
            'bicycle': Decimal('5'),
            'public_transport': Decimal('3'),
            'carpool': Decimal('2'),
            'car': Decimal('0.5')
        }
        
        factor = mode_factors.get(self.transport_mode, Decimal('1'))
        return Decimal(str(self.distance_km)) * factor if self.distance_km else Decimal('0')


class CarbonCredit(models.Model):
    """Model for tracking carbon credits."""
    
    CREDIT_STATUS = (
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    source_trip = models.ForeignKey(
        Trip,
        on_delete=models.SET_NULL,
        related_name='generated_credits',
        null=True,
        blank=True
    )
    owner_type = models.CharField(
        max_length=10,
        choices=(('employee', 'Employee'), ('employer', 'Employer'))
    )
    owner_id = models.IntegerField()  # ID of either EmployeeProfile or EmployerProfile
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=10,
        choices=CREDIT_STATUS,
        default='active'
    )
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.amount} credits for {self.owner_type} ({self.owner_id})"
