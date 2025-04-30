from django.urls import path
from core.views.employee_views import (
    dashboard, trip_log, trips_list, manage_home_location, register_home_location
)

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard, name='employee_dashboard'),
    
    # Trips
    path('trips/', trips_list, name='employee_trips'),
    path('trip/log/', trip_log, name='record_trip'),
    path('home-location/', manage_home_location, name='employee_manage_home_location'),
    path('home-location/register/', register_home_location, name='register_home_location'),
] 