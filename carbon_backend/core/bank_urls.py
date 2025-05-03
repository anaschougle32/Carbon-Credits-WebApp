from django.urls import path
from core.views.bank_views import (
    dashboard as bank_dashboard, 
    dashboard_analytics, 
    employers_list, 
    employer_approval, 
    employer_detail,
    employer_edit,
    trading, 
    transaction_approval, 
    buy_credits,
    BankReportsView,
    export_report,
    generate_report,
    transactions,
    approvals,
    approve_transaction,
    reject_transaction
)

app_name = 'bank'

urlpatterns = [
    path('dashboard/', bank_dashboard, name='bank_dashboard'),
    path('dashboard/analytics/', dashboard_analytics, name='bank_dashboard_analytics'),
    path('employers/', employers_list, name='bank_employers'),
    path('employers/<int:employer_id>/', employer_detail, name='bank_employer_detail'),
    path('employers/<int:employer_id>/edit/', employer_edit, name='bank_employer_edit'),
    path('employers/<int:employer_id>/approval/', employer_approval, name='employer_approval'),
    path('trading/', trading, name='bank_trading'),
    path('trading/<int:transaction_id>/approval/', transaction_approval, name='transaction_approval'),
    path('trading/buy-credits/', buy_credits, name='buy_credits'),
    path('approvals/', approvals, name='bank_approvals'),
    path('approvals/<int:transaction_id>/approve/', approve_transaction, name='approve_transaction'),
    path('approvals/<int:transaction_id>/reject/', reject_transaction, name='reject_transaction'),
    path('reports/', BankReportsView.as_view(), name='bank_reports'),
    path('reports/generate/', generate_report, name='generate_report'),
    path('reports/export/', export_report, name='export_report'),
    path('transactions/', transactions, name='transactions'),
] 