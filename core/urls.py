from django.urls import path
from . import views


urlpatterns = [
    path('', views.WatchlistView.as_view(), name='watchlist'),
    path('mark-watching/<int:item_id>/', views.mark_as_watching, name='mark_watching'),
    path('mark-completed/<int:item_id>/', views.mark_as_completed, name='mark_completed'),
    path('trending/', views.TrendingView.as_view(), name='trending'),
    path('add-to-watchlist/', views.add_to_watchlist, name='add_to_watchlist'),
    path('search/', views.SearchView.as_view(), name='search'),
    # path('recommendations/<str:media_type>/<int:tmdb_id>/', views.RecommendationsView.as_view(), name='recommendations'),
    path('recommendations/', views.RecommendationsView.as_view(), name='recommendations'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('api/analytics/data/', views.analytics_data, name='analytics_data'),
]