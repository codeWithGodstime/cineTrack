from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from core.models import Watchlist
from faker import Faker
import requests
import random
from datetime import timedelta

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seed watchlist data with fake entries using TMDB API'

    def add_arguments(self, parser):
        parser.add_argument('entries', type=int, help='Number of watchlist entries to create')
        parser.add_argument('--user', type=str, help='Username to create entries for (optional)')

    def get_tmdb_data(self, media_type):
        """Fetch random popular movie/TV show from TMDB"""
        api_key = settings.TMDB_API_KEY
        page = random.randint(1, 5)  # Get from first 5 pages of popular items
        
        url = f'https://api.themoviedb.org/3/{media_type}/popular'
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        params = {
            "language": "en-US",
            "page": page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            if data['results']:
                item = random.choice(data['results'])
                
                # Get genres for the item
                detail_url = f'https://api.themoviedb.org/3/{media_type}/{item["id"]}'
                detail_response = requests.get(detail_url, params={'api_key': api_key})
                detail_data = detail_response.json()
                
                genres = ','.join([genre['name'] for genre in detail_data.get('genres', [])])
                
                return {
                    'tmdb_id': item['id'],
                    'title': item.get('title') or item.get('name'),
                    'thumbnail': f"https://image.tmdb.org/t/p/w500{item['poster_path']}" if item['poster_path'] else None,
                    'genre': genres
                }
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error fetching TMDB data: {e}'))
            return None

    def handle(self, *args, **options):
        entries = options['entries']
        username = options.get('user')

        # Get or create user
        if username:
            user = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@gmail.com'}
            )[0]
        else:
            # Create a new user if none specified
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='testpass123'
            )

        self.stdout.write(f'Creating {entries} watchlist entries for user: {user.username}')

        # Generate entries
        for _ in range(entries):
            media_type = random.choice(['movie', 'tv'])
            tmdb_data = self.get_tmdb_data(media_type)
            
            if not tmdb_data:
                continue

            # Random dates within last 6 months
            added_date = timezone.now() - timedelta(days=random.randint(0, 180))
            updated_date = added_date + timedelta(days=random.randint(0, 30))

            # Random status
            is_completed = random.choice([True, False])
            is_currently_watching = False if is_completed else random.choice([True, False])
            
            # Rating only if completed
            user_rating = random.randint(1, 5) if is_completed else None

            Watchlist.objects.create(
                user=user,
                tmdb_id=tmdb_data['tmdb_id'],
                title=tmdb_data['title'],
                media_type=media_type,
                thumbnail=tmdb_data['thumbnail'],
                genre=tmdb_data['genre'],
                is_completed=is_completed,
                is_currently_watching=is_currently_watching,
                user_rating=user_rating,
                added_on=added_date,
                updated_at=updated_date
            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {entries} watchlist entries')
        ) 