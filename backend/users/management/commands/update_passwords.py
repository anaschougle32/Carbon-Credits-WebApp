from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class Command(BaseCommand):
    help = 'Updates passwords from 2023 to 2025 for specified user accounts'

    def handle(self, *args, **kwargs):
        # Define the email addresses and their current passwords
        user_credentials = [
            {
                'email': 'superadmin@carboncredits.com',
                'old_password': 'SuperAdmin2023!',
                'new_password': 'SuperAdmin2025!'
            },
            {
                'email': 'admin@carbonbank.com',
                'old_password': 'BankAdmin2023!',
                'new_password': 'BankAdmin2025!'
            },
            {
                'email': 'jgarcia@greentechsolutions.com',
                'old_password': 'EmployerTest2023!',
                'new_password': 'EmployerTest2025!'
            },
            {
                'email': 'sarah.miller@greentechsolutions.com',
                'old_password': 'EmployeeTest2023!',
                'new_password': 'EmployeeTest2025!'
            }
        ]

        # Counter for successful updates
        updated_count = 0

        # Update each user's password
        for cred in user_credentials:
            email = cred['email']
            new_password = cred['new_password']
            
            try:
                # Get the user by email
                user = User.objects.get(email=email)
                
                # Set the new password
                user.set_password(new_password)
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f'Successfully updated password for {email}'))
                updated_count += 1
                
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'User with email {email} does not exist'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating password for {email}: {str(e)}'))
        
        # Summary message
        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} password(s)'))
        else:
            self.stdout.write(self.style.WARNING('No passwords were updated')) 