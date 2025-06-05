from django.urls import path
from . import views


urlpatterns = [
    path('', views.WatchlistView.as_view(), name='watchlist'),
]