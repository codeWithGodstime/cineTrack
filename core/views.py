from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Watchlist

class WatchlistView(View):
    def get(self, request):
        watchlist = Watchlist.objects.filter(user=request.user).order_by('-added_on')
        completed = Watchlist.objects.filter(user=request.user, is_completed=True).order_by('-updated_at')
        currently_watching = Watchlist.objects.filter(user=request.user, is_currently_watching=True).order_by('-updated_at')
        
        context = {
            'watchlist': watchlist,
            'completed': completed,
            'currently_watching': currently_watching,
        }
        return render(request, 'core/watchlist.html', context)

@login_required
def mark_as_watching(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(Watchlist, id=item_id, user=request.user)
        item.is_currently_watching = True
        item.save()
        messages.success(request, f'"{item.title}" marked as currently watching!')
    return redirect('watchlist')

@login_required
def mark_as_completed(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(Watchlist, id=item_id, user=request.user)
        item.is_completed = True
        item.is_currently_watching = False
        item.save()
        messages.success(request, f'Congratulations! You completed "{item.title}"!')
    return redirect('watchlist')
