from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from users.models import CustomUser, EmployerProfile
from trips.models import Trip, CarbonCredit
from marketplace.models import MarketplaceTransaction
import json
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

@login_required
@user_passes_test(lambda u: u.is_bank_admin)
def dashboard(request):
    """
    Dashboard view for bank administrators.
    """
    # Get basic statistics
    total_users = CustomUser.objects.count()
    total_employers = EmployerProfile.objects.count()
    pending_approvals = EmployerProfile.objects.filter(approved=False).count()
    
    # Credit statistics
    total_credits_raw = CarbonCredit.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_credits = round(float(total_credits_raw), 2)  # Round to 2 decimal places
    
    # Trip statistics
    total_trips = Trip.objects.count()
    
    # Use verification_status field in the filter
    verified_trips_count = Trip.objects.filter(verification_status='verified').count()
    
    # Transaction statistics
    transactions = MarketplaceTransaction.objects.count()
    
    context = {
        'total_users': total_users,
        'total_employers': total_employers,
        'pending_approvals': pending_approvals,
        'total_credits': total_credits,
        'total_trips': total_trips,
        'verified_trips': verified_trips_count,
        'transactions': transactions,
        'page_title': 'Bank Admin Dashboard',
    }
    
    # Get pending employer approvals for the quick view
    pending_employers = EmployerProfile.objects.filter(approved=False).order_by('-created_at')[:5]
    context['pending_employers'] = pending_employers
    
    return render(request, 'bank/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.is_bank_admin)
def dashboard_analytics(request):
    """
    API endpoint for dashboard analytics data (JSON response for charts)
    """
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Credits issued per day
    credits_per_day = (
        CarbonCredit.objects
        .filter(timestamp__gte=start_date)
        .extra(select={'day': "DATE(timestamp)"})
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )
    
    # If no data, create sample data points
    if not credits_per_day:
        # Generate sample data for the requested date range
        sample_credits = []
        for i in range(days):
            current_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            # Random value between 0.5 and 5
            sample_credits.append({
                'day': current_date,
                'total': round(float(i % 5) + 0.5 + (i % 3), 2)  # Simple pattern with some variation
            })
        credits_per_day = sample_credits
    
    # Trips logged per day
    trips_per_day = (
        Trip.objects
        .filter(start_time__gte=start_date)
        .extra(select={'day': "DATE(start_time)"})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    
    # Transport modes distribution
    transport_modes = (
        Trip.objects
        .filter(start_time__gte=start_date)
        .values('transport_mode')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # If no transport modes data, create sample data
    if not transport_modes:
        transport_modes = [
            {'transport_mode': 'bicycle', 'count': 12},
            {'transport_mode': 'work_from_home', 'count': 8},
            {'transport_mode': 'walking', 'count': 6},
            {'transport_mode': 'public_transport', 'count': 5},
            {'transport_mode': 'car', 'count': 3},
        ]
    
    # Transaction volume per day
    transactions_per_day = (
        MarketplaceTransaction.objects
        .filter(created_at__gte=start_date)
        .extra(select={'day': "DATE(created_at)"})
        .values('day')
        .annotate(count=Count('id'), volume=Sum('credit_amount'))
        .order_by('day')
    )
    
    return JsonResponse({
        'credits_per_day': list(credits_per_day),
        'trips_per_day': list(trips_per_day),
        'transport_modes': list(transport_modes),
        'transactions_per_day': list(transactions_per_day),
    })

@login_required
@user_passes_test(lambda u: u.is_bank_admin)
def employers_list(request):
    """
    View for listing and managing employers.
    """
    # Filter by approval status if requested
    approval_filter = request.GET.get('filter')
    
    if approval_filter == 'pending':
        employers = EmployerProfile.objects.filter(approved=False).order_by('-created_at')
    elif approval_filter == 'approved':
        employers = EmployerProfile.objects.filter(approved=True).order_by('-created_at')
    else:
        employers = EmployerProfile.objects.all().order_by('-created_at')
    
    context = {
        'employers': employers,
        'page_title': 'Manage Employers',
        'current_filter': approval_filter,
    }
    
    return render(request, 'bank/employers.html', context)

@login_required
@user_passes_test(lambda u: u.is_bank_admin)
def employer_approval(request, employer_id):
    """
    View for approving or rejecting an employer.
    """
    try:
        employer = EmployerProfile.objects.get(id=employer_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            employer.approved = True
            employer.save()
            # Also update the user's status
            employer.user.approved = True
            employer.user.save()
            return redirect('bank_employers')
        elif action == 'reject':
            # Maybe add rejection notes in the future
            employer.delete()
            return redirect('bank_employers')
            
    except EmployerProfile.DoesNotExist:
        pass
    
    return redirect('bank_employers')

@login_required
@user_passes_test(lambda u: u.is_bank_admin)
def trading(request):
    """
    View for carbon credit trading platform.
    """
    # Get recent transactions
    recent_transactions = MarketplaceTransaction.objects.all().order_by('-created_at')[:10]
    
    # Get transaction statistics
    total_volume = MarketplaceTransaction.objects.aggregate(Sum('credit_amount'))['credit_amount__sum'] or 0
    pending_approvals = MarketplaceTransaction.objects.filter(status='pending').count()
    completed_transactions = MarketplaceTransaction.objects.filter(status='completed').count()
    
    # Check if there are any pending transactions in the recent_transactions list
    has_pending_transactions = any(transaction.status == 'pending' for transaction in recent_transactions)
    
    context = {
        'page_title': 'Carbon Credit Trading',
        'recent_transactions': recent_transactions,
        'total_volume': total_volume,
        'pending_approvals': pending_approvals,
        'completed_transactions': completed_transactions,
        'has_pending_transactions': has_pending_transactions,
    }
    
    return render(request, 'bank/trading.html', context)

@login_required
@user_passes_test(lambda u: u.is_bank_admin)
def transaction_approval(request, transaction_id):
    """
    View for approving or rejecting a transaction.
    """
    try:
        transaction = MarketplaceTransaction.objects.get(id=transaction_id)
        action = request.POST.get('action')
        
        if action == 'approve':
            transaction.status = 'completed'
            transaction.approved_by = request.user
            transaction.completed_at = timezone.now()
            transaction.save()
            return redirect('bank_trading')
        elif action == 'reject':
            transaction.status = 'rejected'
            transaction.save()
            return redirect('bank_trading')
            
    except MarketplaceTransaction.DoesNotExist:
        pass
    
    return redirect('bank_trading') 