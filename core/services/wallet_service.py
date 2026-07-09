from decimal import Decimal
from django.db import transaction
from core.models.wallet import Wallet
import logging

logger = logging.getLogger(__name__)

class InsufficientBalanceError(Exception):
    """Custom exception untuk saldo tidak mencukupi."""
    pass

class InvalidAmountError(Exception):
    """Custom exception untuk nominal yang tidak valid (negatif/nol)."""
    pass

class WalletService:
    """
    Service Layer untuk manajemen Wallet.
    Semua operasi di sini wajib atomic dan aman dari Race Condition.
    """

    @staticmethod
    def create_wallet_for_user(user) -> Wallet:
        """Membuat wallet baru dengan saldo awal 0."""
        return Wallet.objects.create(user=user, balance=Decimal('0.0000'))

    @staticmethod
    def add_balance(user_id: int, amount: Decimal) -> Wallet:
        """
        Menambah saldo. Menggunakan row-level locking (select_for_update)
        untuk memastikan tidak ada Dirty Read atau Lost Update saat concurrent request.
        """
        if amount <= Decimal('0.0000'):
            raise InvalidAmountError("Nominal penambahan harus lebih dari 0.")

        with transaction.atomic():
            # Kunci baris database ini sampai transaksi blok ini selesai!
            wallet = Wallet.objects.select_for_update().get(user_id=user_id)
            wallet.balance += amount
            wallet.save(update_fields=['balance', 'updated_at'])
            
            logger.info(f"Added {amount} to user_id {user_id}. New balance: {wallet.balance}")
            return wallet

    @staticmethod
    def deduct_balance(user_id: int, amount: Decimal) -> Wallet:
        """
        Mengurangi saldo. Mencegah Negative Balance dan Race Condition (Double Spend).
        """
        if amount <= Decimal('0.0000'):
            raise InvalidAmountError("Nominal pengurangan harus lebih dari 0.")

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user_id=user_id)
            
            # Pengecekan saldo dilakukan SETELAH lock diperoleh
            if wallet.balance < amount:
                raise InsufficientBalanceError("Saldo tidak mencukupi untuk melakukan transaksi ini.")
                
            wallet.balance -= amount
            wallet.save(update_fields=['balance', 'updated_at'])
            
            logger.info(f"Deducted {amount} from user_id {user_id}. New balance: {wallet.balance}")
            return wallet