from django.db import models
from django.conf import settings
from decimal import Decimal

class GameRound(models.Model):
    """
    Model untuk menyimpan state setiap putaran permainan.
    Single Source of Truth untuk siklus WAITING -> FLYING -> CRASHED.
    """
    STATUS_CHOICES = [
        ('WAITING', 'Waiting'),
        ('FLYING', 'Flying'),
        ('CRASHED', 'Crashed'),
    ]
    
    # Crash point ditentukan di awal oleh server (saat status WAITING).
    # Klien (Browser) tidak akan tahu nilai ini sampai status menjadi CRASHED.
    crash_point = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='WAITING')
    
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Indexing pada status untuk mempercepat pencarian "putaran mana yang sedang aktif?"
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Round {self.id} - {self.status} (Crash: {self.crash_point}x)"


class Bet(models.Model):
    """
    Model untuk mencatat taruhan user pada setiap putaran.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), # Taruhan berjalan, belum di-cashout
        ('WON', 'Won'),         # User berhasil cashout sebelum hancur
        ('LOST', 'Lost'),       # Hancur sebelum cashout
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bets')
    game_round = models.ForeignKey(GameRound, on_delete=models.CASCADE, related_name='bets')
    
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    cashout_multiplier = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    profit = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)
    half_cashout_done = models.BooleanField(default=False)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Compound index untuk mencegah lambatnya pencarian saat validasi cashout dan filter history
        indexes = [
            models.Index(fields=['user', 'game_round']),
            models.Index(fields=['status', 'game_round']),
        ]
        # Mencegah user melakukan bet 2 kali di ronde yang sama (Data Integrity)
        unique_together = ('user', 'game_round')

    def __str__(self):
        return f"Bet {self.id} | {self.user.username} | {self.amount} | {self.status}"