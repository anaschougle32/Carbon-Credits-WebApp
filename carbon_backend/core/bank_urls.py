from django.urls import path
from core.views.bank_views import dashboard, dashboard_analytics, employers_list, employer_approval, trading, transaction_approval, buy_credits

app_name = 'bank'

urlpatterns = [
    path('dashboard/', dashboard, name='bank_dashboard'),
    path('dashboard/analytics/', dashboard_analytics, name='bank_dashboard_analytics'),
    path('employers/', employers_list, name='bank_employers'),
    path('employers/<int:employer_id>/approval/', employer_approval, name='employer_approval'),
    path('trading/', trading, name='bank_trading'),
    path('trading/<int:transaction_id>/approval/', transaction_approval, name='transaction_approval'),
    path('trading/buy-credits/', buy_credits, name='buy_credits'),
] 