from django.db import transaction
from core.models.wallet import Wallet

# Mengembalikan Custom Exception yang dibutuhkan oleh game_service.py
class InsufficientBalanceError(ValueError):
    pass

class WalletService:
    @staticmethod
    def create_wallet_for_user(user):
        """Membuat dompet baru jika user belum memilikinya."""
        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': 0.0000}
        )
        return wallet

    @staticmethod
    def get_balance(user_id) -> float:
        """Mengambil saldo saat ini (Read Only)."""
        wallet = Wallet.objects.get(user__id=user_id)
        return float(wallet.balance)

    @staticmethod
    def add_balance(user_id, amount: float):
        """Menambah saldo dengan aman menggunakan Database Locking."""
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user__id=user_id)
            wallet.balance += amount
            wallet.save(update_fields=['balance', 'updated_at'])
            return wallet

    @staticmethod
    def deduct_balance(user_id, amount: float):
        """Mengurangi saldo dengan aman. Melempar error jika saldo tidak cukup."""
        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user__id=user_id)
            if wallet.balance < amount:
                # Menggunakan custom error agar game_service.py tidak crash
                raise InsufficientBalanceError("Saldo tidak mencukupi.")
            
            wallet.balance -= amount
            wallet.save(update_fields=['balance', 'updated_at'])
            return wallet