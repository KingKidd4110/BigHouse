# BigHouseWeb/management/commands/create_user_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from BigHouseWeb.models import UserProfile

class Command(BaseCommand):
    help = 'Creates UserProfile instances for all existing users without profiles'
    
    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(userprofile__isnull=True)
        count = 0
        
        for user in users_without_profiles:
            UserProfile.objects.create(user=user)
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} user profiles')
        )
