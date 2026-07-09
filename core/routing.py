from django.urls import path
from core.consumers import GameConsumer

websocket_urlpatterns = [
    # Endpoint WebSocket untuk klien
    path('ws/game/', GameConsumer.as_asgi()),
]