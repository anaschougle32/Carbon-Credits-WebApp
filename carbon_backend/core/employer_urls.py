from django.urls import path
from core.views.employer_views import (
    dashboard, employees_list, locations_list, trading,
    pending_trips, trip_approval, create_transaction, create_offer,
    mark_notification_read, employee_approval, invite_employee,
    location_add, location_edit, location_delete, location_set_primary
)

app_name = 'employer'

urlpatterns = [
    path('dashboard/', dashboard, name='employer_dashboard'),
    path('employees/', employees_list, name='employer_employee_list'),
    path('employees/<int:employee_id>/approval/', employee_approval, name='employee_approval'),
    path('employees/invite/', invite_employee, name='invite_employee'),
    path('locations/', locations_list, name='employer_locations'),
    path('locations/add/', location_add, name='location_add'),
    path('locations/<int:location_id>/edit/', location_edit, name='location_edit'),
    path('locations/<int:location_id>/delete/', location_delete, name='location_delete'),
    path('locations/<int:location_id>/set-primary/', location_set_primary, name='location_set_primary'),
    path('trading/', trading, name='employer_trading'),
    path('trading/create-transaction/', create_transaction, name='create_transaction'),
    path('trading/create-offer/', create_offer, name='create_offer'),
    path('trips/pending/', pending_trips, name='employer_pending_trips'),
    path('trips/<int:trip_id>/approve/', trip_approval, name='employer_trip_approval'),
    path('notifications/<int:notification_id>/mark-read/', mark_notification_read, name='mark_notification_read'),
] 