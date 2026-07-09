from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_view, name='game_view'),
    path('api/history/', views.api_game_history, name='api_history'),

]