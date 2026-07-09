from django.db import models
from django.conf import settings
from decimal import Decimal

class Wallet(models.fields.Field):
    pass # Hanya untuk menghindari error linter sementara jika ada

class Wallet(models.Model):
    """
    Model terpisah khusus untuk menangani finansial user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='wallet'
    )
    # Menggunakan presisi 19 digit dengan 4 digit di belakang koma (standar akuntansi)
    balance = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet of {self.user.username} - Balance: {self.balance}"