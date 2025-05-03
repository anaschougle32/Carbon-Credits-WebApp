from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from users.models import CustomUser, EmployerProfile, EmployeeProfile, Location
from trips.models import CarbonCredit
from decimal import Decimal
import logging

class Command(BaseCommand):
    help = 'Creates test users with different roles and sample data for testing'

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                self.stdout.write(self.style.SUCCESS('Creating test users...'))
                
                # Create test users
                super_admin_user = self._create_super_admin_user()
                bank_admin_user = self._create_bank_admin_user()
                employer_user, employer_profile = self._create_employer_user()
                employee_user, employee_profile = self._create_employee_user(employer_profile)
                
                # Create locations
                self._create_locations(bank_admin_user, employer_user, employee_user, employer_profile)
                
                # Create some carbon credits for the employer
                self._create_sample_credits(employer_profile)
                
                # Make sure all users are approved
                self._ensure_all_users_approved()
                
                # Output credentials for easy testing
                self.stdout.write('\n' + self.style.SUCCESS('Test users created successfully!'))
                self.stdout.write('\n' + self.style.SUCCESS('Credentials:'))
                
                self.stdout.write('\n' + self.style.SUCCESS('Super Admin User:'))
                self.stdout.write(f'Email: superadmin@carboncredits.com')
                self.stdout.write(f'Password: SuperAdmin2023!')
                
                self.stdout.write('\n' + self.style.SUCCESS('Bank Admin User:'))
                self.stdout.write(f'Email: admin@carbonbank.com')
                self.stdout.write(f'Password: BankAdmin2023!')
                
                self.stdout.write('\n' + self.style.SUCCESS('Employer User:'))
                self.stdout.write(f'Email: jgarcia@greentechsolutions.com')
                self.stdout.write(f'Password: EmployerTest2023!')
                
                self.stdout.write('\n' + self.style.SUCCESS('Employee User:'))
                self.stdout.write(f'Email: sarah.miller@greentechsolutions.com')
                self.stdout.write(f'Password: EmployeeTest2023!')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating test users: {str(e)}'))
    
    def _create_super_admin_user(self):
        """Create a super admin user"""
        super_admin_user, created = CustomUser.objects.get_or_create(
            email='superadmin@carboncredits.com',
            defaults={
                'username': 'superadmin',
                'first_name': 'Michael',
                'last_name': 'Thompson',
                'is_super_admin': True,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'approved': True
            }
        )
        
        if created:
            super_admin_user.set_password('SuperAdmin2023!')
            super_admin_user.save()
            self.stdout.write(f'Created super admin user: {super_admin_user.email}')
        else:
            # Update existing user to ensure they're approved
            super_admin_user.approved = True
            super_admin_user.is_active = True
            super_admin_user.save()
            self.stdout.write(f'Updated existing super admin user: {super_admin_user.email}')
            
        return super_admin_user
    
    def _create_bank_admin_user(self):
        """Create a bank admin user"""
        bank_admin_user, created = CustomUser.objects.get_or_create(
            email='admin@carbonbank.com',
            defaults={
                'username': 'bankadmin',
                'first_name': 'Carlos',
                'last_name': 'Rodriguez',
                'is_bank_admin': True,
                'is_active': True,
                'approved': True,
                'is_staff': True
            }
        )
        
        if created:
            bank_admin_user.set_password('BankAdmin2023!')
            bank_admin_user.save()
            self.stdout.write(f'Created bank admin user: {bank_admin_user.email}')
        else:
            # Update existing user to ensure they're approved
            bank_admin_user.approved = True
            bank_admin_user.is_active = True
            bank_admin_user.save()
            self.stdout.write(f'Updated existing bank admin user: {bank_admin_user.email}')
            
        return bank_admin_user
    
    def _create_employer_user(self):
        """Create an employer user with company profile"""
        employer_user, created = CustomUser.objects.get_or_create(
            email='jgarcia@greentechsolutions.com',
            defaults={
                'username': 'jgarcia',
                'first_name': 'Jose',
                'last_name': 'Garcia',
                'is_employer': True,
                'is_active': True,
                'approved': True
            }
        )
        
        if created:
            employer_user.set_password('EmployerTest2023!')
            employer_user.save()
            self.stdout.write(f'Created employer user: {employer_user.email}')
        else:
            # Update existing user to ensure they're approved
            employer_user.approved = True
            employer_user.is_active = True
            employer_user.save()
            self.stdout.write(f'Updated existing employer user: {employer_user.email}')
        
        # Create or update employer profile
        employer_profile, prof_created = EmployerProfile.objects.get_or_create(
            user=employer_user,
            defaults={
                'company_name': 'GreenTech Solutions',
                'registration_number': 'GTH78934',
                'industry': 'Technology',
                'approved': True,
                'wallet_balance': Decimal('25.00')
            }
        )
        
        if not prof_created:
            # Make sure the profile is approved too
            employer_profile.approved = True
            employer_profile.save()
            self.stdout.write(f'Updated employer profile for {employer_user.email}')
        else:
            self.stdout.write(f'Created employer profile for {employer_user.email}')
        
        return employer_user, employer_profile
    
    def _create_employee_user(self, employer_profile):
        """Create an employee user linked to the employer"""
        employee_user, created = CustomUser.objects.get_or_create(
            email='sarah.miller@greentechsolutions.com',
            defaults={
                'username': 'smiller',
                'first_name': 'Sarah',
                'last_name': 'Miller',
                'is_employee': True,
                'is_active': True,
                'approved': True
            }
        )
        
        if created:
            employee_user.set_password('EmployeeTest2023!')
            employee_user.save()
            self.stdout.write(f'Created employee user: {employee_user.email}')
        else:
            # Update existing user to ensure they're approved
            employee_user.approved = True
            employee_user.is_active = True
            employee_user.save()
            self.stdout.write(f'Updated existing employee user: {employee_user.email}')
        
        # Create or update employee profile
        employee_profile, prof_created = EmployeeProfile.objects.get_or_create(
            user=employee_user,
            defaults={
                'employer': employer_profile,
                'employee_id': 'EMP001',
                'approved': True,
                'department': 'Marketing',
                'wallet_balance': Decimal('5.00')
            }
        )
        
        if not prof_created:
            # Make sure the profile is approved too
            employee_profile.approved = True
            employee_profile.save()
            self.stdout.write(f'Updated employee profile for {employee_user.email}')
        else:
            self.stdout.write(f'Created employee profile for {employee_user.email}')
        
        return employee_user, employee_profile
    
    def _create_locations(self, bank_admin_user, employer_user, employee_user, employer_profile):
        """Create sample locations in Boca Raton area"""
        # Bank location (admin office)
        bank_location, created = Location.objects.get_or_create(
            name='Carbon Bank Headquarters',
            created_by=bank_admin_user,
            defaults={
                'latitude': Decimal('26.3683'),
                'longitude': Decimal('-80.1289'),
                'address': '1515 N Federal Hwy, Boca Raton, FL 33432',
                'location_type': 'office',
                'is_primary': True
            }
        )
        if created:
            self.stdout.write(f'Created bank location: {bank_location.name}')
        
        # Employer office location
        employer_office, created = Location.objects.get_or_create(
            name='GreenTech Solutions HQ',
            created_by=employer_user,
            defaults={
                'latitude': Decimal('26.3578'),
                'longitude': Decimal('-80.0831'),
                'address': '900 E Atlantic Ave, Delray Beach, FL 33483',
                'location_type': 'office',
                'employer': employer_profile,
                'is_primary': True
            }
        )
        if created:
            self.stdout.write(f'Created employer office: {employer_office.name}')
        
        # Employee home location
        employee_home, created = Location.objects.get_or_create(
            name='Sarah\'s Home',
            created_by=employee_user,
            defaults={
                'latitude': Decimal('26.3472'),
                'longitude': Decimal('-80.0786'),
                'address': '1801 S Ocean Blvd, Boca Raton, FL 33432',
                'location_type': 'home',
                'is_primary': True
            }
        )
        if created:
            self.stdout.write(f'Created employee home: {employee_home.name}')
    
    def _create_sample_credits(self, employer_profile):
        """Create sample carbon credits for the employer"""
        credits, created = CarbonCredit.objects.get_or_create(
            amount=Decimal('100.00'),
            owner_type='employer',
            owner_id=employer_profile.id,
            defaults={
                'source_trip': None,
                'status': 'active',
                'expiry_date': timezone.now() + timezone.timedelta(days=365)
            }
        )
        
        if created:
            self.stdout.write(f'Created 100 carbon credits for {employer_profile.company_name}')
    
    def _ensure_all_users_approved(self):
        """Make sure all users are approved and active"""
        # Update all users to be approved
        updated_count = CustomUser.objects.update(approved=True, is_active=True)
        self.stdout.write(f'Ensured {updated_count} users are approved and active')
        
        # Update all employer profiles to be approved
        employer_count = EmployerProfile.objects.update(approved=True)
        self.stdout.write(f'Ensured {employer_count} employer profiles are approved')
        
        # Update all employee profiles to be approved
        employee_count = EmployeeProfile.objects.update(approved=True)
        self.stdout.write(f'Ensured {employee_count} employee profiles are approved')