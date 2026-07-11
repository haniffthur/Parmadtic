import json
from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum

from core.models.game import GameRound, Bet
from core.services.wallet_service import WalletService
from core.forms import CustomUserCreationForm

def get_user_context(user):
    if not hasattr(user, 'wallet'):
        WalletService.create_wallet_for_user(user)
    return {'username': user.username, 'balance': user.wallet.balance}

# --- AUTHENTICATION VIEWS ---
def register_view(request):
    if request.user.is_authenticated:
        return redirect('game_view')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                WalletService.create_wallet_for_user(user)
            login(request, user)
            return redirect('game_view')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('game_view')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('game_view')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

@login_required(login_url='/login/')
def logout_view(request):
    logout(request)
    return redirect('login_view')

def game_view(request):
    context = {}
    
    # Jika user sudah login, muat data dompetnya
    if request.user.is_authenticated:
        if not hasattr(request.user, 'wallet'):
            WalletService.create_wallet_for_user(request.user)
        context = {
            'username': request.user.username,
            'balance': request.user.wallet.balance,
        }
    
    # Jika user anonim (belum login), context akan kosong, tapi halaman tetap dirender
    return render(request, 'core/game.html', context)

@login_required(login_url='/login/')
def deposit_view(request):
    return render(request, 'core/deposit.html', get_user_context(request.user))

@login_required(login_url='/login/')
def withdraw_view(request):
    return render(request, 'core/withdraw.html', get_user_context(request.user))

@login_required(login_url='/login/')
def profile_view(request):
    user = request.user
    context = get_user_context(user)
    
    finished_bets = Bet.objects.filter(user=user).exclude(status='PENDING')
    total_bets = finished_bets.count()
    won_bets = finished_bets.filter(status='WON').count()
    lost_bets = total_bets - won_bets
    win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
    
    total_wagered = finished_bets.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.0000')
    total_returned = finished_bets.filter(status='WON').aggregate(Sum('profit'))['profit__sum'] or Decimal('0.0000')
    net_pnl = total_returned - total_wagered
    
    context.update({
        'total_bets': total_bets,
        'won_bets': won_bets,
        'lost_bets': lost_bets,
        'win_rate': round(win_rate, 2),
        'total_wagered': total_wagered,
        'net_pnl': net_pnl,
        'is_profit': net_pnl > 0
    })
    return render(request, 'core/profile.html', context)

# --- INTERNAL API VIEWS (SIMULATOR WALLET) ---
@login_required(login_url='/login/')
def api_game_history(request):
    rounds_query = GameRound.objects.filter(status='CRASHED').order_by('-id')
    paginator = Paginator(rounds_query, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    data = {
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'history': [{'id': r.id, 'crash_point': float(r.crash_point), 'waktu': r.ended_at.strftime("%d %b %Y, %H:%M:%S") if r.ended_at else "-"} for r in page_obj]
    }
    return JsonResponse(data)

@login_required(login_url='/login/')
def api_simulate_deposit(request):
    """Endpoint untuk mensimulasikan top-up saldo secara instan."""
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            amount = Decimal(str(body.get('amount', 0)))
            if amount <= 0:
                return JsonResponse({'success': False, 'message': 'Nominal tidak valid.'})
            if amount > Decimal('100000000'): # Limit edukasi (100 Juta)
                return JsonResponse({'success': False, 'message': 'Maksimal top-up simulasi adalah 100 Juta.'})
                
            WalletService.add_balance(request.user.id, amount)
            return JsonResponse({'success': True, 'message': f'Berhasil simulasi top-up Rp {amount:,.0f}'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid Method'})

@login_required(login_url='/login/')
def api_simulate_withdraw(request):
    """Endpoint untuk mensimulasikan penarikan saldo secara instan."""
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            amount = Decimal(str(body.get('amount', 0)))
            if amount <= 0:
                return JsonResponse({'success': False, 'message': 'Nominal tidak valid.'})
                
            # Logika deduct_balance sudah diproteksi atomic & pengecekan saldo cukup
            WalletService.deduct_balance(request.user.id, amount)
            return JsonResponse({'success': True, 'message': f'Berhasil simulasi penarikan Rp {amount:,.0f}'})
        except ValueError as ve:
            # Mengembalikan error spesifik jika saldo kurang
            return JsonResponse({'success': False, 'message': str(ve)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid Method'})