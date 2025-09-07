# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from .models import UserProfile, Building, House, Tenant, RentPayment, ManagementAlert
from .forms import CustomUserCreationForm, UserProfileForm, BuildingForm, HouseForm, AlertForm

def is_owner_or_superuser(user):
    return user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.user_type == 'owner')

def is_manager_or_above(user):
    return user.is_superuser or (hasattr(user, 'userprofile') and 
                                user.userprofile.user_type in ['manager', 'owner'])

# Create your views here.
def home(request):
    return render(request, 'BigHouseWeb/home.html')

@login_required
def profile_view(request):
    user_profile = request.user.userprofile
    tenant = None
    house = None
    rent_payments = []
    alerts = []
    
    if user_profile.user_type == 'tenant':
        try:
            tenant = Tenant.objects.get(user=request.user)
            house = tenant.house
            rent_payments = RentPayment.objects.filter(tenant=tenant).order_by('-due_date')[:5]
        except Tenant.DoesNotExist:
            pass
        
        # Get alerts for the tenant's building
        if house:
            alerts = ManagementAlert.objects.filter(building=house.building, is_active=True)
    
    context = {
        'user_profile': user_profile,
        'tenant': tenant,
        'house': house,
        'rent_payments': rent_payments,
        'alerts': alerts,
    }
    return render(request, 'bigHouseWeb/profile.html', context)

@login_required
@user_passes_test(is_manager_or_above)
def management_dashboard(request):
    # Get buildings based on user role
    if request.user.is_superuser:
        buildings = Building.objects.all()
        houses = House.objects.all()
    elif request.user.userprofile.user_type == 'owner':
        buildings = Building.objects.filter(owner=request.user)
        houses = House.objects.filter(building__in=buildings)
    else:  # manager
        buildings = Building.objects.filter(managers=request.user.userprofile)
        houses = House.objects.filter(building__in=buildings)
    
    tenants = Tenant.objects.filter(house__in=houses)
    alerts = ManagementAlert.objects.filter(building__in=buildings, is_active=True)
    
    # Forms
    house_form = HouseForm(user=request.user)
    alert_form = AlertForm(user=request.user)
    
    if request.method == 'POST':
        if 'add_house' in request.POST:
            house_form = HouseForm(request.POST, user=request.user)
            if house_form.is_valid():
                house = house_form.save()
                messages.success(request, f'House {house.house_number} added successfully!')
                return redirect('management_dashboard')
        
        elif 'add_alert' in request.POST:
            alert_form = AlertForm(request.POST, user=request.user)
            if alert_form.is_valid():
                alert = alert_form.save()
                messages.success(request, 'Alert created successfully!')
                return redirect('management_dashboard')
    
    context = {
        'buildings': buildings,
        'houses': houses,
        'tenants': tenants,
        'alerts': alerts,
        'house_form': house_form,
        'alert_form': alert_form,
    }
    return render(request, 'BigHouseWeb/management_dashboard.html', context)

@login_required
@user_passes_test(is_owner_or_superuser)
def admin_management(request):
    if not (request.user.is_superuser or request.user.userprofile.user_type == 'owner'):
        return HttpResponseForbidden("You don't have permission to access this page.")
    
    # Get all users for management
    users = User.objects.all().select_related('userprofile')
    
    # Get buildings based on user role
    if request.user.is_superuser:
        buildings = Building.objects.all()
        can_add_owner = True
    else:  # owner
        buildings = Building.objects.filter(owner=request.user)
        can_add_owner = False
    
    building_form = BuildingForm()
    user_form = UserProfileForm()
    
    if request.method == 'POST':
        if 'add_building' in request.POST and request.user.is_superuser:
            building_form = BuildingForm(request.POST)
            if building_form.is_valid():
                building = building_form.save(commit=False)
                building.owner = request.user
                building.save()
                messages.success(request, f'Building {building.name} added successfully!')
                return redirect('admin_management')
        
        elif 'update_user' in request.POST:
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, id=user_id)
            user_form = UserProfileForm(request.POST, instance=user.userprofile)
            
            if user_form.is_valid():
                user_form.save()
                messages.success(request, f'User {user.username} updated successfully!')
                return redirect('admin_management')
    
    context = {
        'users': users,
        'buildings': buildings,
        'building_form': building_form,
        'user_form': user_form,
        'can_add_owner': can_add_owner,
    }
    return render(request, 'BigHouseWeb/admin_management.html', context)

@login_required
@user_passes_test(is_owner_or_superuser)
def delete_building(request, building_id):
    building = get_object_or_404(Building, id=building_id)
    
    # Check permissions
    if not request.user.is_superuser and building.owner != request.user:
        return HttpResponseForbidden("You don't have permission to delete this building.")
    
    # Convert managers back to tenants
    managers = UserProfile.objects.filter(managed_building=building, user_type='manager')
    for manager in managers:
        manager.user_type = 'tenant'
        manager.managed_building = None
        manager.save()
    
    # Delete the building (this will cascade to houses, alerts, etc.)
    building_name = building.name
    building.delete()
    
    messages.success(request, f'Building {building_name} and all associated data deleted successfully.')
    return redirect('admin_management')

@login_required
@user_passes_test(is_manager_or_above)
def delete_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    house = tenant.house
    
    # Check if the user has permission for this tenant's building
    if request.user.is_superuser:
        pass  # Superuser can do anything
    elif request.user.userprofile.user_type == 'owner':
        if house.building.owner != request.user:
            return HttpResponseForbidden("You don't have permission to perform this action.")
    else:  # manager
        if house.building not in Building.objects.filter(managers=request.user.userprofile):
            return HttpResponseForbidden("You don't have permission to perform this action.")
    
    # Free up the house
    house.is_occupied = False
    house.save()
    
    # Delete the tenant
    tenant.delete()
    messages.success(request, 'Tenant removed successfully.')
    return redirect('management_dashboard')

@login_required
@user_passes_test(is_manager_or_above)
def mark_rent_paid(request, payment_id):
    payment = get_object_or_404(RentPayment, id=payment_id)
    
    # Check if the manager has permission for this payment
    if payment.tenant.house.building.manager != request.user:
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('management_dashboard')
    
    payment.status = 'paid'
    payment.paid_date = timezone.now().date()
    payment.save()
    messages.success(request, 'Rent marked as paid.')
    return redirect('management_dashboard')
