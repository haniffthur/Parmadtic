import time
import math
import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction  # Penting untuk me-refresh snapshot database
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Pastikan import Model Bet dan GameRound
from core.models.game import GameRound, Bet
from core.services.game_service import GameService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Menjalankan Autonomous Game Engine (Versi Synchronous Stabil)'

    def handle(self, *args, **options):
        """Titik masuk utama saat menjalankan `python manage.py rungameengine`"""
        self.stdout.write(self.style.SUCCESS('Memulai Game Engine (Sync Mode)...'))
        
        # Bersihkan putaran yang menggantung jika server sebelumnya mati mendadak
        self.cleanup_orphan_rounds()
        
        self.stdout.write(self.style.WARNING('Engine berjalan! Terminal disederhanakan untuk Admin:'))
        try:
            self.engine_loop()
        except KeyboardInterrupt:
            self.stdout.write(self.style.ERROR('\nEngine dihentikan secara manual oleh Admin.'))
        except Exception as e:
            logger.exception("Critical Error pada Game Engine:")
            self.stdout.write(self.style.ERROR(f'\nEngine berhenti karena error kritis: {e}'))

    def cleanup_orphan_rounds(self):
        """Mengubah status game yang menggantung menjadi CRASHED demi konsistensi data."""
        orphans = GameRound.objects.filter(status__in=['WAITING', 'FLYING'])
        for round_obj in orphans:
            GameService.crash_round(round_obj.id)
            self.stdout.write(self.style.WARNING(f'Membersihkan putaran menggantung: ID {round_obj.id}'))

    def engine_loop(self):
        """Loop utama penggerak detak jantung game (Game Tick)."""
        channel_layer = get_channel_layer()
        room_group_name = 'crash_game_room'

        while True:
            # OPTIMASI: Ambil 10 history terbaru hanya 1 kali setiap putaran dimulai
            # (Menghemat query database daripada memanggilnya 10x per detik)
            recent_history = GameService.get_recent_history(limit=10)
            
            # =========================================================
            # 1. FASE WAITING (Persiapan Taruhan)
            # =========================================================
            current_round = GameService.create_new_round()
            round_id = current_round.id
            crash_point = float(current_round.crash_point) 
            
            print(f"\n==================================================")
            print(f">> [RONDE {round_id}] Dibuat! Target Hancur: {crash_point:.2f}x")
            print(f"==================================================")

            countdown = 5.0
            while countdown > 0:
                if round(countdown, 1).is_integer():
                    print(f"   [WAITING] Memulai dalam {int(countdown)}...")
                
                # FORCE REFRESH: Hindari Stale Snapshot DB di Long-Running Process
                transaction.commit()
                
                # HITUNG PEMAIN AKTIF (Yang statusnya masih PENDING)
                # Menggunakan .count() sangat cepat karena dikonversi menjadi SELECT COUNT(*) oleh SQL
                active_players = Bet.objects.filter(game_round_id=round_id, status='PENDING').count()
                
                async_to_sync(channel_layer.group_send)(room_group_name, {
                    'type': 'game_tick',
                    'payload': {
                        'state': 'WAITING',
                        'round_id': round_id,
                        'countdown': round(countdown, 1),
                        'history': recent_history,
                        'active_players': active_players
                    }
                })
                time.sleep(0.1) 
                countdown -= 0.1

            # =========================================================
            # 2. FASE FLYING (Pesawat Mengudara)
            # =========================================================
            print(">> [FLYING] Pesawat lepas landas! Sedang mengudara...")
            self.set_round_flying(round_id)
            started_at = timezone.now()
            
            is_crashed = False
            current_multiplier = 1.00

            while not is_crashed:
                # Kalkulasi eksponensial berdasarkan waktu berlalu
                elapsed_time = (timezone.now() - started_at).total_seconds()
                current_multiplier = math.exp(0.06 * elapsed_time)
                current_multiplier = round(current_multiplier, 2)

                # Evaluasi titik hancur
                if current_multiplier >= crash_point:
                    current_multiplier = crash_point
                    is_crashed = True
                
                # FORCE REFRESH: Sangat penting di sini karena pemain akan menekan tombol Cashout
                transaction.commit()
                
                # HITUNG SISA PEMAIN (Angka akan menurun real-time jika ada yang berhasil Cashout)
                active_players = Bet.objects.filter(game_round_id=round_id, status='PENDING').count()
                
                async_to_sync(channel_layer.group_send)(room_group_name, {
                    'type': 'game_tick',
                    'payload': {
                        'state': 'FLYING',
                        'round_id': round_id,
                        'multiplier': f"{current_multiplier:.2f}",
                        'history': recent_history,
                        'active_players': active_players
                    }
                })
                
                if not is_crashed:
                    time.sleep(0.1)

            # =========================================================
            # 3. FASE CRASHED (Pesawat Meledak)
            # =========================================================
            print(f">> [CRASHED] BOOM! Sesuai target, hancur di {crash_point:.2f}x!\n")
            
            # Eksekusi logika bisnis: Menghanguskan taruhan PENDING menjadi LOST
            GameService.crash_round(round_id)
            
            # Refresh history untuk memasukkan ronde yang baru saja hancur ini
            latest_history = GameService.get_recent_history(limit=10)
            
            async_to_sync(channel_layer.group_send)(room_group_name, {
                'type': 'game_tick',
                'payload': {
                    'state': 'CRASHED',
                    'round_id': round_id,
                    'multiplier': f"{crash_point:.2f}",
                    'history': latest_history,
                    'active_players': 0  # Saat crash, otomatis 0 karena game berakhir
                }
            })
            
            # Jeda sebelum memulai putaran baru
            time.sleep(3.0)

    def set_round_flying(self, round_id):
        """Fungsi pembantu untuk mengubah status ronde menjadi FLYING."""
        game_round = GameRound.objects.get(id=round_id)
        game_round.status = 'FLYING'
        game_round.started_at = timezone.now()
        game_round.save(update_fields=['status', 'started_at'])