# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Building, House, ManagementAlert

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone_number']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # UserProfile is created by the signal, now update it
            user_profile = user.userprofile
            user_profile.phone_number = self.cleaned_data['phone_number']
            user_profile.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['user_type', 'profile_picture', 'phone_number', 'managed_building']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show buildings for manager assignment
        self.fields['managed_building'].queryset = Building.objects.all()
        # Only allow changing to manager or tenant, not owner
        self.fields['user_type'].choices = [
            ('tenant', 'Tenant'),
            ('manager', 'Property Manager'),
        ]

class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['name', 'address']

class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = ['building', 'house_number', 'rent_amount']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Show only buildings owned by the current user
            if user.userprofile.user_type == 'owner':
                self.fields['building'].queryset = Building.objects.filter(owner=user)
            # Show all buildings for superusers
            elif user.is_superuser:
                self.fields['building'].queryset = Building.objects.all()
            else:
                self.fields['building'].queryset = Building.objects.none()

class AlertForm(forms.ModelForm):
    class Meta:
        model = ManagementAlert
        fields = ['building', 'title', 'message']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Show only buildings the user has access to
            if user.userprofile.user_type == 'owner':
                self.fields['building'].queryset = Building.objects.filter(owner=user)
            elif user.userprofile.user_type == 'manager':
                self.fields['building'].queryset = Building.objects.filter(managers=user.userprofile)
            elif user.is_superuser:
                self.fields['building'].queryset = Building.objects.all()
            else:
                self.fields['building'].queryset = Building.objects.none()
