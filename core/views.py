from django.shortcuts import render
from django.views.generic import View


class WatchlistView(View):
    def get(self, request):
        return render(request, 'core/watchlist.html')
