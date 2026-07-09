from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from core.services.wallet_service import WalletService
from core.models.game import GameRound

@login_required(login_url='/admin/login/')
def game_view(request):
    user = request.user
    if not hasattr(user, 'wallet'):
        WalletService.create_wallet_for_user(user)
        
    context = {
        'username': user.username,
        'balance': user.wallet.balance,
    }
    return render(request, 'core/game.html', context)

@login_required(login_url='/admin/login/')
def api_game_history(request):
    """
    REST API Endpoint untuk Server-Side Pagination History.
    Mencegah browser/server crash saat data mencapai ratusan ribu baris.
    """
    # Ambil data yang CRASHED saja, urutkan dari yang terbaru
    rounds_query = GameRound.objects.filter(status='CRASHED').order_by('-id')
    
    # Batasi 20 data per halaman (KISS & Performance Principle)
    paginator = Paginator(rounds_query, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    data = {
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'history': [
            {
                'id': r.id,
                'crash_point': float(r.crash_point),
                # Format waktu yang manusiawi
                'waktu': r.ended_at.strftime("%d %b %Y, %H:%M:%S") if r.ended_at else "-"
            } for r in page_obj
        ]
    }
    return JsonResponse(data)