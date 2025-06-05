from django.urls import path
from . import views


urlpatterns = [
    path('', views.WatchlistView.as_view(), name='watchlist'),
    path('mark-watching/<int:item_id>/', views.mark_as_watching, name='mark_watching'),
    path('mark-completed/<int:item_id>/', views.mark_as_completed, name='mark_completed'),
    path('trending/', views.TrendingView.as_view(), name='trending'),
    path('add-to-watchlist/', views.add_to_watchlist, name='add_to_watchlist'),
]