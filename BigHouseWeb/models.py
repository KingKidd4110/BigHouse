# models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal

class UserProfile(models.Model):
    USER_TYPES = (
        ('tenant', 'Tenant'),
        ('manager', 'Property Manager'),
        ('owner', 'Property Owner'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='tenant')
    profile_picture = models.ImageField(upload_to='media/profile_pics/images', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    managed_building = models.ForeignKey('Building', on_delete=models.SET_NULL, null=True, blank=True, related_name='managers')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
    
    def clean(self):
        # A manager must have a building assigned
        if self.user_type == 'manager' and not self.managed_building:
            raise ValidationError('Managers must be assigned to a building.')
        
        # Non-managers should not have a managed building
        if self.user_type != 'manager' and self.managed_building:
            self.managed_building = None


class Building(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_buildings')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name
    
    def house_count(self):
        return self.houses.count()


class House(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='houses')
    house_number = models.CharField(max_length=10)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_occupied = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('building', 'house_number')
    
    def __str__(self):
        return f"{self.building.name} - {self.house_number}"


class Tenant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    house = models.OneToOneField(House, on_delete=models.SET_NULL, null=True, blank=True)
    move_in_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.house}"


class RentPayment(models.Model):
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('due', 'Due'),
        ('overdue', 'Overdue'),
    )
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='rent_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='due')

    def calculate_next_due_date(self):
        if self.paid_date and self.amount and self.tenant.house.rent_amount:
            # Calculate how many months were paid for
            months_paid = (self.amount / self.tenant.house.rent_amount).normalize()
            
            if months_paid % 1 == 0:  # Whole number of months
                months = int(months_paid)
                next_due = self.paid_date + relativedelta(months=+months)
                return next_due, None
            else:
                # Partial payment - calculate full months and remainder
                full_months = int(months_paid)
                remainder = self.amount % self.tenant.house.rent_amount
                next_due = self.paid_date + relativedelta(months=+full_months)
                return next_due, remainder
        return None, None


    
    def __str__(self):
        return f"{self.tenant} - {self.due_date} - {self.status}"

class ManagementAlert(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='alerts')
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.message[:20]}"


# Create user profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
