from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # System config endpoints (admin only)
    path('config/', views.SystemConfigListView.as_view(), name='config_list'),
    path('config/<int:pk>/', views.SystemConfigDetailView.as_view(), name='config_detail'),
    
    # Admin-specific endpoints
    path('admin/stats/', views.AdminStatsView.as_view(), name='admin_stats'),
    path('admin/dashboard/stats/', views.AdminDashboardView.as_view(), name='admin_dashboard_stats'),
    path('admin/employers/pending/', views.PendingEmployersView.as_view(), name='pending_employers'),
    path('admin/transactions/pending/', views.PendingTransactionsView.as_view(), name='pending_transactions'),
    path('admin/bank-admins/', views.BankAdminCreateView.as_view(), name='create_bank_admin'),
] 