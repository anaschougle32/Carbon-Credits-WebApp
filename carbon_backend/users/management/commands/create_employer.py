from django.core.management.base import BaseCommand
from users.models import CustomUser, EmployerProfile
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates a new employer'

    def handle(self, *args, **kwargs):
        email = 'testfauemployer@gmail.com'
        
        try:
            with transaction.atomic():
                # Delete existing user if exists
                CustomUser.objects.filter(email=email).delete()
                
                # Create the user
                user = CustomUser.objects.create_user(
                    username=email,
                    email=email,
                    password='testfau123!',
                    first_name='Test_FAU',
                    last_name='Employer',
                    is_employer=True,
                    is_staff=True,
                    is_active=True,
                    approved=True
                )
                
                # Create the employer profile
                employer = EmployerProfile.objects.create(
                    user=user,
                    company_name='Test FAU Company',
                    approved=True,
                    initial_credits_allocated=False,
                    wallet_balance=0
                )
                
                self.stdout.write(self.style.SUCCESS('Successfully created employer:'))
                self.stdout.write(f"Email: {user.email}")
                self.stdout.write(f"Company: {employer.company_name}")
                self.stdout.write(f"Password: testfau123!")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating employer: {str(e)}')) 