from django.db import models
from django.utils import timezone
from users.models import CustomUser, EmployerProfile


class MarketOffer(models.Model):
    """Model for carbon credit selling offers on the marketplace."""
    
    OFFER_STATUS = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    )
    
    seller = models.ForeignKey(
        EmployerProfile, 
        on_delete=models.CASCADE, 
        related_name='market_offers'
    )
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    price_per_credit = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=OFFER_STATUS,
        default='active'
    )
    expiry_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.seller.company_name}: {self.credit_amount} credits at {self.price_per_credit} each"
    
    def save(self, *args, **kwargs):
        # Calculate total price before saving
        if not self.total_price:
            self.total_price = self.credit_amount * self.price_per_credit
        super().save(*args, **kwargs)


class MarketplaceTransaction(models.Model):
    """Model for tracking carbon credit transactions between employers."""
    
    TRANSACTION_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    offer = models.ForeignKey(
        MarketOffer, 
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    seller = models.ForeignKey(
        EmployerProfile, 
        on_delete=models.CASCADE, 
        related_name='sold_transactions'
    )
    buyer = models.ForeignKey(
        EmployerProfile, 
        on_delete=models.CASCADE, 
        related_name='bought_transactions'
    )
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=TRANSACTION_STATUS,
        default='pending'
    )
    admin_approval_required = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='approved_transactions',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.buyer.company_name} buying {self.credit_amount} credits from {self.seller.company_name}"
    
    def save(self, *args, **kwargs):
        # Set seller from offer if not specified
        if not self.seller_id and self.offer:
            self.seller = self.offer.seller
        
        # Calculate total price if not specified
        if not self.total_price and self.offer and self.credit_amount:
            self.total_price = self.credit_amount * self.offer.price_per_credit
        
        # Set admin approval flag for large transactions
        if self.total_price >= 1000:  # Example threshold
            self.admin_approval_required = True
            
        super().save(*args, **kwargs)


class TransactionNotification(models.Model):
    """Model for notifying users about transaction status changes."""
    
    transaction = models.ForeignKey(
        MarketplaceTransaction,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='transaction_notifications'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Notification for {self.user.email} about transaction #{self.transaction.id}"


# Signal handlers for transaction status changes
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=MarketplaceTransaction)
def create_transaction_notifications(sender, instance, created, **kwargs):
    """Create notifications when transaction status changes."""
    if created:
        # New transaction created
        # Notify seller about new pending transaction
        TransactionNotification.objects.create(
            transaction=instance,
            user=instance.seller.user,
            message=f"New transaction #{instance.id}: {instance.buyer.company_name} wants to buy {instance.credit_amount} credits for ${instance.total_price}."
        )
        
        # Notify bank admins about pending approval
        bank_admins = CustomUser.objects.filter(is_bank_admin=True)
        for admin in bank_admins:
            TransactionNotification.objects.create(
                transaction=instance,
                user=admin,
                message=f"Transaction #{instance.id} requires your approval: {instance.buyer.company_name} buying {instance.credit_amount} credits from {instance.seller.company_name}."
            )
    
    elif not created and instance.status in ['completed', 'rejected', 'cancelled']:
        # Status changed to completed, rejected or cancelled
        # Notify buyer
        TransactionNotification.objects.create(
            transaction=instance,
            user=instance.buyer.user,
            message=f"Transaction #{instance.id} has been {instance.status}. {instance.credit_amount} credits purchase from {instance.seller.company_name} for ${instance.total_price}."
        )
        
        # Notify seller
        TransactionNotification.objects.create(
            transaction=instance,
            user=instance.seller.user,
            message=f"Transaction #{instance.id} has been {instance.status}. Sale of {instance.credit_amount} credits to {instance.buyer.company_name} for ${instance.total_price}."
        )
