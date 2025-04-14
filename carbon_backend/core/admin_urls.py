from django.urls import path
from core.views import admin_views

urlpatterns = [
    # Dashboard
    path('', admin_views.dashboard, name='admin_dashboard'),
    
    # User management
    path('users/', admin_views.users_list, name='admin_users'),
    path('users/create/', admin_views.create_user, name='admin_create_user'),
    path('users/<int:user_id>/', admin_views.user_detail, name='admin_user_detail'),
    path('users/<int:user_id>/approve/', admin_views.approve_user, name='admin_approve_user'),
    path('users/<int:user_id>/reject/', admin_views.reject_user, name='admin_reject_user'),
    path('users/hierarchy/', admin_views.user_hierarchy, name='admin_user_hierarchy'),
    
    # Reports
    path('reports/', admin_views.reports, name='admin_reports'),
    
    # Dashboard components that load dynamically
    path('recent-trips/', admin_views.dashboard_recent_trips, name='admin_dashboard_recent_trips'),
] 