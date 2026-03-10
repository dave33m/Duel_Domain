from django.urls import path
from src.views import player_views

urlpatterns = [
    path("me/", player_views.my_profile, name='my-profile'),
    path("<uuid:player_id>/", player_views.get_profile, name='get-profile'),
    path("me/update/", player_views.update_profile, name='update-profile'),
    path("leaderboard/", player_views.leaderboard, name='leaderboard'),
    path("search/", player_views.search_players, name='search-players'),
    path("me/stats/", player_views.my_stats, name='my-stats'),
  
]
