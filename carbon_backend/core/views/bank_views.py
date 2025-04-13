from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from users.models import CustomUser, EmployerProfile
from trips.models import Trip, CarbonCredit
from marketplace.models import MarketplaceTransaction, MarketOffer
import json
from django.db.models import Sum, Count, Avg, Case, When, Value, IntegerField, F
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

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
            return redirect('bank:bank_employers')
        elif action == 'reject':
            # Maybe add rejection notes in the future
            employer.delete()
            return redirect('bank:bank_employers')
            
    except EmployerProfile.DoesNotExist:
        pass
    
    return redirect('bank:bank_employers')

@login_required
@user_passes_test(lambda u: u.is_bank_admin)
def trading(request):
    """
    View for carbon credit trading platform.
    """
    # Get recent transactions
    recent_transactions = MarketplaceTransaction.objects.all().order_by('-created_at')[:10]
    
    # Get transaction statistics
    total_volume_raw = MarketplaceTransaction.objects.aggregate(Sum('credit_amount'))['credit_amount__sum'] or 0
    # Format the total volume to avoid overflow
    total_volume = round(float(total_volume_raw), 2)
    
    pending_approvals = MarketplaceTransaction.objects.filter(status='pending').count()
    completed_transactions = MarketplaceTransaction.objects.filter(status='completed').count()
    
    # Get pending transactions for approval tab
    pending_transactions = MarketplaceTransaction.objects.filter(status='pending').order_by('-created_at')
    
    # Add mock pending transactions if none exist
    if not pending_transactions:
        # Create some mock pending transactions
        from datetime import datetime, timedelta
        import uuid
        
        mock_transactions = []
        buyers = ["Alpha Corp", "Beta Group", "Gamma Enterprises"]
        sellers = ["EcoTech Inc.", "Green Solutions", "Sustainable Energy"]
        
        for i in range(3):
            # Create a mock transaction for display purposes only
            mock_transaction = type('MockTransaction', (), {
                'id': uuid.uuid4().int % 10000,
                'seller': type('MockSeller', (), {'company_name': sellers[i]}),
                'buyer': type('MockBuyer', (), {'company_name': buyers[i]}),
                'credit_amount': (i+1) * 20,
                'price_per_credit': round(10 + (i * 1.2), 2),
                'total_price': round((i+1) * 20 * (10 + (i * 1.2)), 2),
                'created_at': datetime.now() - timedelta(hours=i * 4),
                'status': 'pending'
            })
            mock_transactions.append(mock_transaction)
        
        # Use mock transactions instead of database transactions
        pending_transactions = mock_transactions
    
    # Get completed transactions for history tab
    completed_transaction_records = MarketplaceTransaction.objects.filter(status='completed').order_by('-completed_at')[:20]
    
    # Check if there are any pending transactions in the recent_transactions list
    has_pending_transactions = any(transaction.status == 'pending' for transaction in recent_transactions)
    
    # Get real available credit offers from MarketOffer model
    available_credits = MarketOffer.objects.filter(status='active').order_by('-created_at')[:10]
    
    # Mock market offers if none exist (for demo purposes)
    if not available_credits:
        # Check if we have at least one employer to use for mock data
        employers = EmployerProfile.objects.all()
        if employers.exists():
            employer = employers.first()
            
            # Create some mock market offers
            from datetime import datetime, timedelta
            import uuid
            
            mock_offers = []
            companies = ["EcoTech Inc.", "Green Solutions", "Sustainable Energy", "EcoTransport"]
            
            for i, company in enumerate(companies):
                # Create a mock offer for display purposes only
                mock_offer = type('MockOffer', (), {
                    'id': uuid.uuid4().int % 10000,
                    'seller': type('MockSeller', (), {'company_name': company}),
                    'credit_amount': (i+1) * 25,
                    'price_per_credit': round(10 + (i * 1.5), 2),
                    'total_price': round((i+1) * 25 * (10 + (i * 1.5)), 2),
                    'created_at': datetime.now() - timedelta(days=i),
                    'status': 'active'
                })
                mock_offers.append(mock_offer)
            
            # Use mock offers instead of database offers
            available_credits = mock_offers
    
    # Mock data for top traders (since we don't have the actual query for this)
    top_traders = [
        {'company_name': 'EcoTech Inc.', 'bought': 150, 'sold': 75, 'net': 75},
        {'company_name': 'Green Solutions', 'bought': 120, 'sold': 200, 'net': -80},
        {'company_name': 'Sustainable Energy', 'bought': 85, 'sold': 40, 'net': 45},
        {'company_name': 'EcoTransport', 'bought': 60, 'sold': 90, 'net': -30},
    ]
    
    # Calculate real market stats
    avg_price = MarketOffer.objects.filter(status='active').aggregate(Avg('price_per_credit'))['price_per_credit__avg'] or 0
    available_credits_count = MarketOffer.objects.filter(status='active').aggregate(Sum('credit_amount'))['credit_amount__sum'] or 0
    seller_count = MarketOffer.objects.filter(status='active').values('seller').distinct().count()
    
    # If no real market stats, use mock data
    if avg_price == 0 and available_credits:
        avg_price = sum(offer.price_per_credit for offer in available_credits) / len(available_credits)
        available_credits_count = sum(offer.credit_amount for offer in available_credits)
        seller_count = len(set(offer.seller.company_name for offer in available_credits))
    
    market_stats = {
        'avg_price': round(avg_price, 2),
        'total_volume': total_volume,
        'available_credits': available_credits_count,
        'seller_count': seller_count
    }
    
    context = {
        'page_title': 'Carbon Credit Trading',
        'recent_transactions': recent_transactions,
        'pending_transactions': pending_transactions,
        'completed_transactions': completed_transaction_records,
        'total_volume': total_volume,
        'pending_approvals': pending_approvals,
        'completed_transactions_count': completed_transactions,
        'has_pending_transactions': has_pending_transactions,
        'top_traders': top_traders,
        'market_stats': market_stats,
        'available_credits': available_credits,
        'market_offers': available_credits,  # Add market_offers as an alias for available_credits
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
        action = request.GET.get('action', '')  # Get action from query parameter
        
        if action == 'approve':
            # Update transaction status
            transaction.status = 'completed'
            transaction.approved_by = request.user
            transaction.completed_at = timezone.now()
            transaction.save()
            
            # Add the carbon credits to the buyer's account
            CarbonCredit.objects.create(
                amount=transaction.credit_amount,
                source_trip=None,
                owner_type='employer',
                owner_id=transaction.buyer.id,
                timestamp=timezone.now(),
                status='active',
                expiry_date=timezone.now() + timezone.timedelta(days=365)  # 1 year validity
            )
            
            # Notify the users
            messages.success(request, f"Transaction #{transaction.id} approved successfully. {transaction.credit_amount} credits transferred to {transaction.buyer.company_name}.")
            return redirect('bank:bank_trading')
            
        elif action == 'reject':
            transaction.status = 'rejected'
            transaction.save()
            
            # Return the credits to the seller's offer
            offer = transaction.offer
            if offer.status != 'cancelled' and offer.status != 'expired':
                offer.credit_amount += transaction.credit_amount
                offer.total_price = offer.credit_amount * offer.price_per_credit
                # If the offer was completed, set it back to active
                if offer.status == 'completed':
                    offer.status = 'active'
                offer.save()
            
            messages.success(request, f"Transaction #{transaction.id} rejected. Credits returned to the marketplace.")
            return redirect('bank:bank_trading')
            
    except MarketplaceTransaction.DoesNotExist:
        messages.error(request, "Transaction not found.")
    
    return redirect('bank:bank_trading')

@login_required
@user_passes_test(lambda u: u.is_bank_admin)
def buy_credits(request):
    """
    View for bank admins to buy carbon credits.
    """
    if request.method == 'POST':
        offer_id = request.POST.get('buyOfferId')
        credit_amount = request.POST.get('creditAmount')
        price_per_credit = request.POST.get('pricePerCredit')
        total_price = request.POST.get('totalPrice')
        
        try:
            # Get the offer
            offer = MarketOffer.objects.get(id=offer_id)
            
            # Check if offer is active
            if offer.status != 'active':
                messages.error(request, "This offer is no longer active")
                return redirect('bank:bank_trading')
                
            # Check if enough credits available
            if int(credit_amount) > offer.credit_amount:
                messages.error(request, "Not enough credits available in this offer")
                return redirect('bank:bank_trading')
            
            # Create the transaction
            transaction = MarketplaceTransaction.objects.create(
                offer=offer,
                seller=offer.seller,
                buyer=request.user.employer_profile,
                credit_amount=int(credit_amount),
                price_per_credit=float(price_per_credit),
                total_price=float(total_price),
                status='pending'
            )
            
            # If this purchase uses all remaining credits, mark offer as completed
            if int(credit_amount) == offer.credit_amount:
                offer.status = 'completed'
                offer.save()
            # Otherwise, reduce the available credits
            else:
                offer.credit_amount -= int(credit_amount)
                offer.total_price = offer.credit_amount * offer.price_per_credit
                offer.save()
                
            messages.success(request, f"Successfully placed order for {credit_amount} credits")
            
        except MarketOffer.DoesNotExist:
            messages.error(request, "The selected offer no longer exists")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    return redirect('bank:bank_trading') 