from django.core.management.base import BaseCommand
from users.models import CustomUser, EmployerProfile, Location
from decimal import Decimal

class Command(BaseCommand):
    help = 'Sets up FAU as employer location and employee locations in Boca Raton'

    def handle(self, *args, **options):
        try:
            # Get or create FAU employer
            fau_employer, created = EmployerProfile.objects.get_or_create(
                company_name='Test_FAU Employer',
                defaults={
                    'company_description': 'Florida Atlantic University - Test Employer',
                    'company_size': '1000+',
                    'industry': 'Education'
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS('Created FAU employer profile'))
            
            # Create FAU office location
            fau_location, created = Location.objects.get_or_create(
                name='FAU Boca Raton Campus',
                employer=fau_employer,
                defaults={
                    'latitude': Decimal('26.3716'),
                    'longitude': Decimal('-80.1010'),
                    'address': '777 Glades Rd, Boca Raton, FL 33431',
                    'location_type': 'office',
                    'is_primary': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS('Created FAU office location'))
            
            # Create employee home locations in Boca Raton
            employee_locations = [
                {
                    'name': 'Boca Raton Apartments',
                    'latitude': Decimal('26.3683'),
                    'longitude': Decimal('-80.1289'),
                    'address': '5535 N Military Trail, Boca Raton, FL 33496',
                },
                {
                    'name': 'Boca Raton Condos',
                    'latitude': Decimal('26.3578'),
                    'longitude': Decimal('-80.0831'),
                    'address': '900 E Atlantic Ave, Boca Raton, FL 33432',
                },
                {
                    'name': 'Boca Raton Homes',
                    'latitude': Decimal('26.3472'),
                    'longitude': Decimal('-80.0786'),
                    'address': '1801 S Ocean Blvd, Boca Raton, FL 33432',
                }
            ]
            
            for loc in employee_locations:
                location, created = Location.objects.get_or_create(
                    name=loc['name'],
                    defaults={
                        'latitude': loc['latitude'],
                        'longitude': loc['longitude'],
                        'address': loc['address'],
                        'location_type': 'home',
                        'is_primary': True
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created employee location: {loc["name"]}'))
            
            self.stdout.write(self.style.SUCCESS('Successfully set up FAU and employee locations'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up locations: {str(e)}')) 