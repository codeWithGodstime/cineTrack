import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone


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


class AnalyticsView(LoginRequiredMixin, View):
    def get(self, request):
        # Basic statistics
        total_watched = Watchlist.objects.filter(user=request.user, is_completed=True).count()
        total_items = Watchlist.objects.filter(user=request.user).count()
        completion_rate = (total_watched / total_items * 100) if total_items > 0 else 0
        
        # Media split
        movies_count = Watchlist.objects.filter(user=request.user, is_completed=True, media_type='movie').count()
        tv_count = Watchlist.objects.filter(user=request.user, is_completed=True, media_type='tv').count()
        
        # Top rated titles
        top_rated = Watchlist.objects.filter(
            user=request.user,
            is_completed=True,
            user_rating__isnull=False
        ).order_by('-user_rating')[:5]

        # Calculate watch streak
        completed_items = Watchlist.objects.filter(
            user=request.user,
            is_completed=True
        ).order_by('updated_at')
        
        current_streak = 0
        longest_streak = 0
        current_date = None
        
        for item in completed_items:
            item_date = item.updated_at.date()
            if current_date is None or item_date == current_date + timedelta(days=1):
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            elif item_date > current_date + timedelta(days=1):
                current_streak = 1
            current_date = item_date

        context = {
            'total_watched': total_watched,
            'total_items': total_items,
            'completion_rate': round(completion_rate, 1),
            'movies_count': movies_count,
            'tv_count': tv_count,
            'top_rated': top_rated,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
        }
        
        return render(request, 'core/analytics.html', context)


@login_required
def analytics_data(request):
    # Genre watch rate
    genre_data = defaultdict(int)
    completed_items = Watchlist.objects.filter(user=request.user, is_completed=True)
    for item in completed_items:
        genres = item.genre.split(',') if item.genre else []
        for genre in genres:
            genre = genre.strip()
            if genre:
                genre_data[genre] += 1

    # Watch time by month
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_data = defaultdict(int)
    completed_by_month = completed_items.filter(
        updated_at__gte=six_months_ago
    ).order_by('updated_at')
    
    for item in completed_by_month:
        month_key = item.updated_at.strftime('%Y-%m')
        monthly_data[month_key] += 1

    # Backlog tracker
    added_by_month = defaultdict(int)
    completed_by_month_count = defaultdict(int)
    all_items = Watchlist.objects.filter(user=request.user)
    
    for item in all_items:
        added_month = item.added_on.strftime('%Y-%m')
        added_by_month[added_month] += 1
        if item.is_completed:
            completed_month = item.updated_at.strftime('%Y-%m')
            completed_by_month_count[completed_month] += 1

    data = {
        'genre_data': dict(genre_data),
        'monthly_data': dict(monthly_data),
        'backlog_data': {
            'added': dict(added_by_month),
            'completed': dict(completed_by_month_count)
        }
    }
    
    return JsonResponse(data)


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        # Calculate user statistics
        total_watched = Watchlist.objects.filter(user=request.user, is_completed=True).count()
        avg_rating = Watchlist.objects.filter(
            user=request.user,
            user_rating__isnull=False
        ).aggregate(Avg('user_rating'))['user_rating__avg']
        
        # Calculate favorite genres
        genre_counts = defaultdict(int)
        for item in Watchlist.objects.filter(user=request.user):
            genres = item.genre.split(',') if item.genre else []
            for genre in genres:
                genre = genre.strip()
                if genre:
                    genre_counts[genre] += 1
        
        favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Determine watch persona
        persona = "Casual Viewer"
        if total_watched > 100:
            persona = "Movie Buff"
        elif total_watched > 50:
            persona = "Regular Watcher"
        
        if avg_rating and avg_rating > 4:
            persona = "Cinephile"
        
        context = {
            'user': request.user,
            'total_watched': total_watched,
            'avg_rating': round(avg_rating, 1) if avg_rating else None,
            'favorite_genres': favorite_genres,
            'watch_persona': persona,
            'movies_count': Watchlist.objects.filter(user=request.user, media_type='movie', is_completed=True).count(),
            'tv_count': Watchlist.objects.filter(user=request.user, media_type='tv', is_completed=True).count(),
        }
        
        return render(request, 'core/profile.html', context)


class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'core/profile_edit.html', {'user': request.user})

    def post(self, request):
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
