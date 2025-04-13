from django.urls import path
from core.views import admin_views

urlpatterns = [
    path('', admin_views.dashboard, name='admin_dashboard'),
    path('users/', admin_views.users_list, name='admin_users'),
    path('reports/', admin_views.reports, name='admin_reports'),
    path('recent-trips/', admin_views.dashboard_recent_trips, name='admin_dashboard_recent_trips'),
] 