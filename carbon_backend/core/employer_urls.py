from django.urls import path
from core.views.employer_views import dashboard, employees_list, locations_list, trading

urlpatterns = [
    path('dashboard/', dashboard, name='employer_dashboard'),
    path('employees/', employees_list, name='employer_employees'),
    path('locations/', locations_list, name='employer_locations'),
    path('trading/', trading, name='employer_trading'),
] 