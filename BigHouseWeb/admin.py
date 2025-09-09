# admin.py
from django.contrib import admin
from .models import UserProfile, Building, House, Tenant, RentPayment, ManagementAlert, ContactUs

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'phone_number']
    list_filter = ['user_type']

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'owner', 'house_count', 'created_at']
    list_filter = ['owner', 'created_at']
    
    def house_count(self, obj):
        return obj.houses.count()
    house_count.short_description = 'Number of Houses'

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ['building', 'house_number', 'rent_amount', 'is_occupied']
    list_filter = ['building', 'is_occupied']

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['user', 'house', 'move_in_date']
    list_filter = ['house__building']

@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'amount', 'due_date', 'paid_date', 'status']
    list_filter = ['status', 'due_date']

@admin.register(ManagementAlert)
class ManagementAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'building', 'created_at', 'is_active']
    list_filter = ['building', 'is_active']

@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'submitted_at']
    list_filter = ['submitted_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['submitted_at']
