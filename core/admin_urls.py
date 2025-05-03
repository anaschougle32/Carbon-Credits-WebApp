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
    
    # Employer management
    path('employers/', admin_views.employers_list, name='admin_employers'),
    path('employers/pending/', admin_views.employers_list, name='admin_pending_employers'),
    
    # Reports
    path('reports/', admin_views.reports, name='admin_reports'),
    path('reports/summary/', admin_views.reports, {'type': 'summary'}, name='admin_reports_summary'),
    path('reports/carbon-credits/', admin_views.reports, {'type': 'credits'}, name='admin_reports_carbon_credits'),
    path('reports/trips/', admin_views.reports, {'type': 'trips'}, name='admin_reports_trips'),
    path('reports/users/', admin_views.reports, {'type': 'users'}, name='admin_reports_users'),
    path('reports/custom/', admin_views.reports, {'type': 'custom'}, name='admin_reports_custom'),
    path('reports/export/', admin_views.export_reports, name='admin_export_reports'),
    
    # Dashboard components that load dynamically
    path('recent-trips/', admin_views.dashboard_recent_trips, name='admin_dashboard_recent_trips'),
] 