# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Building, House, ManagementAlert, ContactUs

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
        fields = ['profile_picture', 'phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': 'Your phone number'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].required = False
        
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
            elif user.userprofile.user_type == 'manager':
                self.fields['building'].queryset = Building.objects.filter(managers=user.userprofile)
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


class ContactUsForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered dark:bg-slate-700 dark:text-white dark:border-slate-600',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered dark:bg-slate-700 dark:text-white dark:border-slate-600',
                'placeholder': 'Your Email'
            }),
            'message': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered h-24 dark:bg-slate-700 dark:text-white dark:border-slate-600',
                'placeholder': 'Your Message'
            }),
        }
