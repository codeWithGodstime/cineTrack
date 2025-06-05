from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Watchlist(models.Model):
    MOVIE = 'movie'
    TV = 'tv'

    MEDIA_TYPE_CHOICES = [
        (MOVIE, 'Movie'),
        (TV, 'TV Show'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist_items')
    title = models.CharField(max_length=255)
    tmdb_id = models.IntegerField()
    thumbnail = models.URLField()
    genre = models.CharField(max_length=255)  
    is_completed = models.BooleanField(default=False)
    is_currently_watching = models.BooleanField(default=False)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    added_on = models.DateTimeField(auto_now_add=True)
    user_rating = models.PositiveIntegerField(null=True, blank=True)
    personal_notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'tmdb_id', 'media_type']

    def __str__(self):
        return f"{self.title} ({self.media_type}) - {self.user.username}"
