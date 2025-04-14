from django.urls import path
from core.views.employee_views import dashboard, trip_log, trips_list, manage_home_location

urlpatterns = [
    path('dashboard/', dashboard, name='employee_dashboard'),
    path('trip/log/', trip_log, name='employee_trip_log'),
    path('trips/', trips_list, name='employee_trips'),
    path('home-location/', manage_home_location, name='employee_manage_home_location'),
] 