from django.urls import path
from core.views.employee_views import dashboard, trip_log, trips_list

urlpatterns = [
    path('dashboard/', dashboard, name='employee_dashboard'),
    path('trip/log/', trip_log, name='employee_trip_log'),
    path('trips/', trips_list, name='employee_trips'),
] 