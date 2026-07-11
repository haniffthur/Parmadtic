import json
import logging
from decimal import Decimal, InvalidOperation
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from core.models import user
from core.services.game_service import GameService, GameLogicError
from core.services.wallet_service import InsufficientBalanceError

logger = logging.getLogger(__name__)

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Dijalankan ketika browser mencoba terhubung ke WebSocket."""
        self.room_group_name = 'crash_game_room'

        # Gabungkan klien ke dalam grup broadcast Redis
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Dijalankan ketika browser terputus."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Menerima pesan dari klien (Bet / Cashout)."""
        user = self.scope["user"]
        
        # Tolak jika user belum login (AnonymousUser)
        if not user.is_authenticated:
            await self.send_error("Anda harus login untuk bermain.")
            return
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'bet':
                amount = Decimal(str(data.get('amount', '0')))
                round_id = data.get('round_id')
                await self.handle_bet(user, round_id, amount)

            elif action == 'cashout':
                bet_id = data.get('bet_id')
                multiplier = Decimal(str(data.get('multiplier', '1.00')))
                await self.handle_cashout(user, bet_id, multiplier)
            elif action == 'cancel_bet':
                try:
                    await database_sync_to_async(
                        GameService.cancel_bet
                    )(
                        data["bet_id"],
                        user.id
                    )

                    await self.send(text_data=json.dumps({
                        "type": "cancel_success",
                        "message": "Taruhan berhasil dibatalkan."
                    }))

                except GameLogicError as e:
                    await self.send_error(str(e))

                except Exception as e:
                    logger.exception(e)
                    await self.send_error("Terjadi kesalahan sistem.")
                    
            elif action == "cashout_half":
                try:
                    multiplier = Decimal(
                        str(data.get("multiplier"))
                    )
                    profit = await database_sync_to_async(
                        GameService.cashout_half
                    )(
                        data["bet_id"],
                        user.id,
                        multiplier
                    )
                    await self.send(text_data=json.dumps({

                        "type": "cashout_half_success",

                        "profit": str(profit),

                        "message": f"Berhasil cair 50%"

                    }))
                except GameLogicError as e:
                    await self.send_error(str(e))
                except Exception as e:
                    logger.exception(e)
                    await self.send_error("Terjadi kesalahan sistem.")

                except json.JSONDecodeError:
                    await self.send_error("Format data tidak valid.")
                except InvalidOperation:
                    await self.send_error("Format nominal angka tidak valid.")
                except Exception as e:
                    logger.error(f"WebSocket Receive Error: {e}")
                    await self.send_error("Terjadi kesalahan sistem internal.")
        except json.JSONDecodeError:
            await self.send_error("Format data tidak valid.")
        except InvalidOperation:
            await self.send_error("Format nominal angka tidak valid.")
        except Exception as e:
            logger.error(f"WebSocket Receive Error: {e}")
            await self.send_error("Terjadi kesalahan sistem internal.")

    async def handle_bet(self, user, round_id, amount):
        try:
            # Membungkus operasi database ke dalam thread sinkronus
            bet = await database_sync_to_async(GameService.place_bet)(user, round_id, amount)
            await self.send(text_data=json.dumps({
                'type': 'bet_success',
                'bet_id': bet.id,
                'amount': str(bet.amount),
                'message': 'Taruhan berhasil dipasang.'
            }))
        except (GameLogicError, InsufficientBalanceError) as e:
            await self.send_error(str(e))

    async def handle_cashout(self, user, bet_id, multiplier):
        try:
            bet = await database_sync_to_async(GameService.cashout)(user, bet_id, multiplier)
            await self.send(text_data=json.dumps({
                'type': 'cashout_success',
                'bet_id': bet.id,
                'profit': str(bet.profit),
                'message': f'Berhasil ditarik pada {multiplier}x!'
            }))
        except GameLogicError as e:
            await self.send_error(str(e))

    async def send_error(self, message):
        """Fungsi helper untuk mengirim pesan error ke klien ini saja."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    # FUNGSI BROADCAST (Dipanggil oleh Game Engine dari Redis Channel Layer)
    async def game_tick(self, event):
        """Mengirim data real-time (state & multiplier) ke browser."""
        # BUGFIX: Kita harus membungkus kembali payload dengan 'type' 
        # agar dikenali oleh if condition di AlpineJS
        await self.send(text_data=json.dumps({
            'type': 'game_tick',
            'payload': event['payload']
        }))