import time
import math
import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from core.models.game import GameRound
from core.services.game_service import GameService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Menjalankan Autonomous Game Engine (Versi Synchronous Stabil untuk Windows)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Memulai Game Engine (Sync Mode)...'))
        self.cleanup_orphan_rounds()
        self.stdout.write(self.style.WARNING('Engine berjalan! Terminal disederhanakan untuk Admin:'))
        try:
            self.engine_loop()
        except KeyboardInterrupt:
            self.stdout.write(self.style.ERROR('\nEngine dihentikan secara manual.'))

    def cleanup_orphan_rounds(self):
        orphans = GameRound.objects.filter(status__in=['WAITING', 'FLYING'])
        for round in orphans:
            GameService.crash_round(round.id)

    def engine_loop(self):
        channel_layer = get_channel_layer()
        room_group_name = 'crash_game_room'

        while True:
            # OPTIMASI: Ambil 10 history terbaru hanya 1 kali setiap putaran dimulai
            recent_history = GameService.get_recent_history(limit=10)
            
            # 1. FASE WAITING
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
                
                async_to_sync(channel_layer.group_send)(room_group_name, {
                    'type': 'game_tick',
                    'payload': {
                        'state': 'WAITING',
                        'round_id': round_id,
                        'countdown': round(countdown, 1),
                        'history': recent_history # <- SUNTIKKAN DATA HISTORY
                    }
                })
                time.sleep(0.1) 
                countdown -= 0.1

            # 2. FASE FLYING
            print(">> [FLYING] Pesawat lepas landas! Sedang mengudara...")
            self.set_round_flying(round_id)
            started_at = timezone.now()
            
            is_crashed = False
            current_multiplier = 1.00

            while not is_crashed:
                elapsed_time = (timezone.now() - started_at).total_seconds()
                current_multiplier = math.exp(0.06 * elapsed_time)
                current_multiplier = round(current_multiplier, 2)

                if current_multiplier >= crash_point:
                    current_multiplier = crash_point
                    is_crashed = True
                
                async_to_sync(channel_layer.group_send)(room_group_name, {
                    'type': 'game_tick',
                    'payload': {
                        'state': 'FLYING',
                        'round_id': round_id,
                        'multiplier': f"{current_multiplier:.2f}",
                        'history': recent_history # <- SUNTIKKAN DATA HISTORY
                    }
                })
                
                if not is_crashed:
                    time.sleep(0.1)

            # 3. FASE CRASHED
            print(f">> [CRASHED] BOOM! Sesuai target, hancur di {crash_point:.2f}x!\n")
            GameService.crash_round(round_id)
            
            # Kita panggil ulang untuk mendapatkan list terbaru HARI INI termasuk yang baru saja hancur
            latest_history = GameService.get_recent_history(limit=10)
            
            async_to_sync(channel_layer.group_send)(room_group_name, {
                'type': 'game_tick',
                'payload': {
                    'state': 'CRASHED',
                    'round_id': round_id,
                    'multiplier': f"{crash_point:.2f}",
                    'history': latest_history # <- SUNTIKKAN HISTORY TERBARU
                }
            })
            
            time.sleep(3.0)

    def set_round_flying(self, round_id):
        game_round = GameRound.objects.get(id=round_id)
        game_round.status = 'FLYING'
        game_round.started_at = timezone.now()
        game_round.save(update_fields=['status', 'started_at'])