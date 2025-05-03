from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from trips.models import Trip, CarbonCredit
from users.models import EmployeeProfile, EmployerProfile
from marketplace.models import MarketOffer, EmployeeCreditOffer

User = get_user_model()

class Command(BaseCommand):
    help = 'Clean up database by removing non-essential data while preserving admin users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--preserve-admin',
            action='store_true',
            help='Preserve admin user accounts',
        )
        parser.add_argument(
            '--preserve-employer',
            action='store_true',
            help='Preserve employer accounts',
        )

    def handle(self, *args, **options):
        preserve_admin = options['preserve_admin']
        preserve_employer = options['preserve_employer']
        
        self.stdout.write(self.style.NOTICE('Starting database cleanup...'))
        
        # Delete marketplace data
        market_offers_count = MarketOffer.objects.count()
        MarketOffer.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {market_offers_count} market offers'))
        
        employee_offers_count = EmployeeCreditOffer.objects.count()
        EmployeeCreditOffer.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {employee_offers_count} employee credit offers'))
        
        # Delete trip data
        trips_count = Trip.objects.count()
        Trip.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {trips_count} trips'))
        
        # Delete carbon credits
        credits_count = CarbonCredit.objects.count()
        CarbonCredit.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {credits_count} carbon credits'))
        
        # Delete users based on options
        if preserve_admin:
            admin_users = User.objects.filter(is_superuser=True)
            admin_usernames = list(admin_users.values_list('username', flat=True))
            self.stdout.write(self.style.NOTICE(f'Preserving admin users: {", ".join(admin_usernames)}'))
            
            # Delete non-admin users
            non_admin_count = User.objects.exclude(is_superuser=True).count()
            User.objects.exclude(is_superuser=True).delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {non_admin_count} non-admin users'))
        elif preserve_employer:
            # Preserve employer users and their profiles
            employer_users = User.objects.filter(employer_profile__isnull=False)
            employer_usernames = list(employer_users.values_list('username', flat=True))
            self.stdout.write(self.style.NOTICE(f'Preserving employer users: {", ".join(employer_usernames)}'))
            
            # Delete non-employer users except admins
            non_employer_count = User.objects.filter(
                employer_profile__isnull=True, 
                is_superuser=False
            ).count()
            User.objects.filter(
                employer_profile__isnull=True,
                is_superuser=False
            ).delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {non_employer_count} non-employer users'))
        else:
            # Full cleanup - delete all users
            users_count = User.objects.count()
            User.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted all {users_count} users'))
        
        self.stdout.write(self.style.SUCCESS('Database cleanup completed')) 