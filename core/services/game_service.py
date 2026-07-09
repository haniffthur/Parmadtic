import secrets
from decimal import Decimal, ROUND_FLOOR
from django.db import transaction
from django.utils import timezone
from core.models.game import GameRound, Bet
from core.services.wallet_service import WalletService, InsufficientBalanceError
import logging

logger = logging.getLogger(__name__)

class GameLogicError(Exception):
    """Custom exception untuk pelanggaran aturan game (e.g., telat pasang taruhan, double cashout)."""
    pass

class GameService:
    
    @staticmethod
    def generate_crash_point(house_edge_percentage: Decimal = Decimal('1.00')) -> Decimal:
        """
        Menghasilkan Crash Point secara kriptografis menggunakan konsep RTP (Return to Player).
        Edukasi: Algoritma ini meniru standar Crash Game di industri (Provably Fair Concept).
        """
        # 1. Gunakan SystemRandom untuk True RNG (Kriptografis), bukan pseudo-random biasa.
        rng = secrets.SystemRandom()
        r = rng.random()  # Menghasilkan float antara 0.0 sampai 1.0 (eksklusif)
        
        # Mencegah division by zero
        if r >= 0.9999999999:
            r = 0.9999999999
            
        rtp_factor = (Decimal('100.00') - house_edge_percentage) / Decimal('100.00')
        
        # Formula Probabilitas: Crash Point = RTP / (1 - r)
        # Semakin mendekati 1 nilai 'r', semakin tinggi multiplier-nya.
        crash_value = rtp_factor / Decimal(str(1.0 - r))
        
        # Format ke 2 digit di belakang koma, dengan minimal nilai 1.00
        # Jika crash_value < 1.00 (misal karena RNG dan house edge bertabrakan), maka Instant Crash!
        final_crash = max(Decimal('1.00'), crash_value.quantize(Decimal('0.01'), rounding=ROUND_FLOOR))
        return final_crash

    @staticmethod
    def create_new_round() -> GameRound:
        """Membuat putaran baru, menentukan titik hancur (dirahasiakan dari frontend)."""
        crash_point = GameService.generate_crash_point(house_edge_percentage=Decimal('1.00'))
        game_round = GameRound.objects.create(
            status='WAITING',
            crash_point=crash_point
        )
        logger.info(f"Putaran {game_round.id} dibuat. Crash Point Rahasia: {crash_point}x")
        return game_round

    @staticmethod
    def place_bet(user, game_round_id: int, amount: Decimal) -> Bet:
        """
        Memasang taruhan. Mengecek status WAITING dan saldo secara Atomic.
        """
        if amount <= Decimal('0.00'):
            raise GameLogicError("Nominal taruhan tidak valid.")

        with transaction.atomic():
            # Lock round agar status tidak berubah saat kita mengeceknya
            game_round = GameRound.objects.select_for_update().get(id=game_round_id)
            
            if game_round.status != 'WAITING':
                raise GameLogicError("Terlambat! Permainan sudah dimulai atau telah berakhir.")
            
            # Potong saldo user (akan raise InsufficientBalanceError jika tidak cukup)
            WalletService.deduct_balance(user.id, amount)
            
            # Buat record Bet
            bet = Bet.objects.create(
                user=user,
                game_round=game_round,
                amount=amount,
                status='PENDING'
            )
            return bet

    @staticmethod
    def cashout(user, bet_id: int, current_multiplier: Decimal) -> Bet:
        """
        Menarik taruhan (Cashout). Ini adalah fungsi paling rentan terhadap serangan.
        Wajib Atomic dan Strict Database Locking.
        """
        with transaction.atomic():
            # Lock tabel Bet ini untuk mencegah Concurrent Request Attack (Multi-tab)
            bet = Bet.objects.select_for_update().get(id=bet_id, user_id=user.id)
            
            if bet.status != 'PENDING':
                raise GameLogicError("Taruhan ini sudah ditarik atau telah hancur.")
                
            # Lock round untuk memastikan permainan masih berjalan (FLYING)
            game_round = GameRound.objects.select_for_update().get(id=bet.game_round_id)
            
            if game_round.status != 'FLYING':
                raise GameLogicError("Permainan belum terbang atau sudah hancur!")

            # Keamanan Tambahan: 
            # Frontend mengirimkan multiplier tempat ia menekan cashout.
            # Pastikan multiplier tersebut TIDAK melebihi crash_point sebenarnya (mencegah manipulasi packet).
            if current_multiplier >= game_round.crash_point:
                raise GameLogicError("Permainan sudah hancur di titik ini (Late Request).")

            # Kalkulasi profit dan update status
            profit = bet.amount * current_multiplier
            
            bet.status = 'WON'
            bet.cashout_multiplier = current_multiplier
            bet.profit = profit
            bet.save(update_fields=['status', 'cashout_multiplier', 'profit'])
            
            # Tambahkan saldo ke dompet (Modal + Profit)
            WalletService.add_balance(user.id, profit)
            
            return bet

    @staticmethod
    def crash_round(game_round_id: int):
        """
        Dipanggil saat waktu terbang menyentuh crash_point.
        Mengubah status game dan menghanguskan semua taruhan yang masih PENDING.
        """
        with transaction.atomic():
            game_round = GameRound.objects.select_for_update().get(id=game_round_id)
            
            if game_round.status == 'CRASHED':
                return game_round # Mencegah double-crash execution
                
            game_round.status = 'CRASHED'
            game_round.ended_at = timezone.now()
            game_round.save(update_fields=['status', 'ended_at'])
            
            # OPTIMASI PERFORMA: Bulk Update. 
            # Tidak me-looping ratusan query, cukup 1 query massal.
            Bet.objects.filter(
                game_round=game_round, 
                status='PENDING'
            ).update(status='LOST')
            
            return game_round
        
    @staticmethod
    def get_recent_history(limit: int = 10) -> list:
        """
        Mengambil riwayat crash point dari putaran yang sudah hancur.
        Dioptimasi: Menggunakan list comprehension dan .values_list() agar tidak meload full ORM object.
        """
        # Keamanan: HANYA mengambil status CRASHED agar crash_point putaran saat ini tidak bocor
        recent_rounds = GameRound.objects.filter(status='CRASHED').order_by('-id')[:limit]
        return [float(round.crash_point) for round in recent_rounds]