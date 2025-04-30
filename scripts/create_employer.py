import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carbon_backend.settings')
django.setup()

from users.models import CustomUser, EmployerProfile

def create_employer():
    try:
        # Create the user
        user = CustomUser.objects.create_user(
            username='testfauemployer@gmail.com',
            email='testfauemployer@gmail.com',
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
            phone='1234567890',
            position='Test Head',
            approved=True
        )
        
        print(f"Successfully created employer:")
        print(f"Email: {user.email}")
        print(f"Company: {employer.company_name}")
        print(f"Position: {employer.position}")
        
    except Exception as e:
        print(f"Error creating employer: {str(e)}")

if __name__ == '__main__':
    create_employer() 