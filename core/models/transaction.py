from django.db import models
from django.conf import settings
from decimal import Decimal

class DepositTransaction(models.Model):
    """
    Model untuk menyimpan riwayat transaksi deposit dari Midtrans.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
    order_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    snap_token = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Index krusial agar pencarian dari Webhook berjalan O(1)
        indexes = [
            models.Index(fields=['order_id']),
        ]

    def __str__(self):
        return f"{self.order_id} - {self.user.username} - {self.amount} - {self.status}"