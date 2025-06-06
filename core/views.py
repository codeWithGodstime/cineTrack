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


class SearchView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '')
        media_type = request.GET.get('type', 'movie')
        page = request.GET.get('page', 1)
        results = []
        total_pages = 0

        if query:
            api_key = settings.TMDB_API_KEY
            url = f'https://api.themoviedb.org/3/search/{media_type}'
            params = {
                'api_key': api_key,
                'query': query,
                'page': page,
                'include_adult': False,
                'language': 'en-US'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                total_pages = data.get('total_pages', 0)

        context = {
            'results': results,
            'query': query,
            'media_type': media_type,
            'current_page': int(page),
            'total_pages': total_pages,
            'has_next': int(page) < total_pages,
            'has_prev': int(page) > 1,
        }
        
        return render(request, 'core/search.html', context)


class RecommendationsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        api_key = settings.TMDB_API_KEY
        
        media_type = request.GET.get('type', 'movie')
        tmdb_id = request.GET.get('tmdb_id', '')
        
        # Get details of the original item
        details_url = f'https://api.themoviedb.org/3/{media_type}/{tmdb_id}'
        details_params = {
            'api_key': api_key,
            'language': 'en-US'
        }
        details_response = requests.get(details_url, params=details_params)
        item_details = details_response.json() if details_response.status_code == 200 else None

        # Get recommendations
        recommendations_url = f'https://api.themoviedb.org/3/{media_type}/{tmdb_id}/recommendations'
        recommendations_params = {
            'api_key': api_key,
            'language': 'en-US',
            'page': 1
        }
        recommendations_response = requests.get(recommendations_url, params=recommendations_params)
        recommendations = recommendations_response.json().get('results', []) if recommendations_response.status_code == 200 else []

        # Get similar items
        similar_url = f'https://api.themoviedb.org/3/{media_type}/{tmdb_id}/similar'
        similar_params = {
            'api_key': api_key,
            'language': 'en-US',
            'page': 1
        }
        similar_response = requests.get(similar_url, params=similar_params)
        similar = similar_response.json().get('results', []) if similar_response.status_code == 200 else []

        context = {
            'item': item_details,
            'recommendations': recommendations[:8],  # Limit to 8 items
            'similar': similar[:8],  # Limit to 8 items
            'media_type': media_type
        }
        
        return render(request, 'core/recommendations.html', context)
