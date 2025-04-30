from django.urls import path
from core.views.employee_views import (
    dashboard,
    trip_log,
    trips_list,
    register_home_location,
    manage_home_location
)

urlpatterns = [
    # Main dashboard
    path('dashboard/', dashboard, name='employee_dashboard'),
    # Trip management
    path('trips/', trips_list, name='employee_trips'),
    path('trips/log/', trip_log, name='record_trip'),
    path('trips/home/', manage_home_location, name='manage_home_location'),
    path('trips/home/register/', register_home_location, name='register_home_location'),
] 