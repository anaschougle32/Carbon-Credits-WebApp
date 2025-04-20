from django.urls import path
from core.views.employee_views import dashboard, trip_log, trips_list, manage_home_location, profile, update_profile, change_password, update_home_location, marketplace

urlpatterns = [
    path('dashboard/', dashboard, name='employee_dashboard'),
    path('trip/log/', trip_log, name='employee_trip_log'),
    path('trips/', trips_list, name='employee_trips'),
    path('home-location/', manage_home_location, name='employee_manage_home_location'),
    path('home-location/update/', update_home_location, name='employee_update_home_location'),
    
    # Profile
    path('profile/', profile, name='employee_profile'),
    path('profile/update/', update_profile, name='employee_update_profile'),
    path('profile/change-password/', change_password, name='employee_change_password'),
    
    # Marketplace
    path('marketplace/', marketplace, name='employee_marketplace'),
] 