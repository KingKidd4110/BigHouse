from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('management/', views.management_dashboard, name='management_dashboard'),
    path('admin-management/', views.admin_management, name='admin_management'),
    path('tenant/delete/<int:tenant_id>/', views.delete_tenant, name='delete_tenant'),
    path('building/delete/<int:building_id>/', views.delete_building, name='delete_building'),
    path('rent/mark_paid/<int:payment_id>/', views.mark_rent_paid, name='mark_rent_paid'),
]
