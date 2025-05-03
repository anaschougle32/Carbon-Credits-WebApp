from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from random import choice, randint, uniform
import datetime

from users.models import CustomUser, EmployeeProfile, EmployerProfile, Location
from trips.models import Trip, CarbonCredit

class Command(BaseCommand):
    help = 'Creates sample trip data for testing charts and dashboards'

    def add_arguments(self, parser):
        parser.add_argument('--trips', type=int, default=50, help='Number of trips to create')
        parser.add_argument('--days', type=int, default=180, help='Number of days in the past to distribute trips')

    def handle(self, *args, **options):
        fake = Faker()
        num_trips = options['trips']
        days_range = options['days']
        
        # Get employees
        employees = EmployeeProfile.objects.all()
        if not employees.exists():
            self.stdout.write(self.style.ERROR('No employees found. Please create employees first.'))
            return
        
        # Get or create sample locations
        home_locations = []
        work_locations = []
        
        for employee in employees:
            # Get or create home location
            home_loc, created = Location.objects.get_or_create(
                created_by=employee.user,
                location_type='home',
                defaults={
                    'name': f"{employee.user.first_name}'s Home",
                    'address': fake.address(),
                    'latitude': uniform(26.0, 26.5),
                    'longitude': uniform(-80.2, -80.0)
                }
            )
            home_locations.append(home_loc)
            
            # Get or create work location for employer
            if employee.employer:
                work_loc, created = Location.objects.get_or_create(
                    created_by=employee.employer.user,
                    location_type='work',
                    defaults={
                        'name': f"{employee.employer.company_name} Office",
                        'address': fake.address(),
                        'latitude': uniform(26.1, 26.4),
                        'longitude': uniform(-80.15, -80.05)
                    }
                )
                work_locations.append(work_loc)
        
        if not home_locations or not work_locations:
            self.stdout.write(self.style.ERROR('Could not find or create locations.'))
            return
        
        # Transport mode weights - make public transport and carpool more common
        transport_weights = {
            'public_transport': 0.5,
            'carpool': 0.3,
            'personal_vehicle': 0.2,
        }
        
        # Get all transport modes
        transport_modes = [mode[0] for mode in Trip.TRANSPORT_MODES]
        
        # Create trips
        trips_created = 0
        now = timezone.now()
        
        for _ in range(num_trips):
            # Choose random employee
            employee = choice(employees)
            
            # Choose random home location
            home_loc = choice([loc for loc in home_locations if loc.created_by == employee.user])
            
            # Choose random work location from employee's employer
            employer_work_locs = [loc for loc in work_locations if loc.created_by == employee.employer.user]
            if not employer_work_locs:
                # Fallback to any work location
                work_loc = choice(work_locations) if work_locations else None
            else:
                work_loc = choice(employer_work_locs)
            
            if not home_loc or not work_loc:
                continue
            
            # Random date in the past X days
            random_days = randint(0, days_range)
            trip_date = (now - datetime.timedelta(days=random_days)).date()
            
            # Random transport mode weighted by preference
            transport_mode = choice(transport_modes)
            
            # Random distance between 5 and 25 km
            distance = round(uniform(5, 25), 1)
            
            # Create Trip
            trip = Trip.objects.create(
                employee=employee,
                trip_date=trip_date,
                start_location=home_loc,
                end_location=work_loc,
                transport_mode=transport_mode,
                distance_km=distance,
                carbon_savings=round(distance * 0.2, 2),  # Simple calculation
                credits_earned=round(distance * 0.1, 2),  # Simple calculation
                verification_status=choice(['pending', 'verified', 'verified', 'verified'])  # More verified than pending
            )
            
            # Create carbon credit for verified trips
            if trip.verification_status == 'verified':
                CarbonCredit.objects.create(
                    trip=trip,
                    user=employee.user,
                    amount=trip.credits_earned,
                    created_at=now - datetime.timedelta(days=random_days),
                    status='active'
                )
            
            trips_created += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {trips_created} sample trips')) 