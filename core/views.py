import requests
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings


from .models import Watchlist

class WatchlistView(LoginRequiredMixin, View):
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


class TrendingView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        api_key = settings.TMDB_API_KEY
        type = self.request.GET.get("type") if self.request.GET.get('type') else 'movie'
        time_window = self.request.GET.get('time_window') if self.request.GET.get('time_window') else 'week'
        
        url = f'https://api.themoviedb.org/3/trending/{type}/{time_window}?api_key={api_key}'
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        response = requests.get(url, headers=headers)
        data = response.json()
        template = 'core/trending-movie.html' if type == 'movie' else 'core/trending-tv.html'
        movies = data['results']
        return render(request, template, {'movies': movies})

@login_required
def add_to_watchlist(request):
    if request.method == 'POST':
        tmdb_id = request.POST.get('tmdb_id')
        title = request.POST.get('title')
        media_type = request.POST.get('media_type')
        poster_path = request.POST.get('poster_path')

        # Check if already in watchlist
        if not Watchlist.objects.filter(user=request.user, tmdb_id=tmdb_id, media_type=media_type).exists():
            # Create new watchlist item
            Watchlist.objects.create(
                user=request.user,
                tmdb_id=tmdb_id,
                title=title,
                media_type=media_type,
                thumbnail=f'https://image.tmdb.org/t/p/w500{poster_path}'
            )
            messages.success(request, f'"{title}" added to your watchlist!')
        else:
            messages.info(request, f'"{title}" is already in your watchlist.')

    return redirect('trending')
