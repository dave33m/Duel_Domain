from django.urls import path
from src.views import game_views

urlpatterns = [
    path("create/", game_views.create_game, name='create-game'),
    path("list/", game_views.list_games, name='list-games'),
    path("<uuid:game_id>/", game_views.get_game, name='get-game'),
    path("<uuid:game_id>/update/", game_views.update_game, name='update-game'),
    path("<uuid:game_id>/delete/", game_views.delete_game, name='delete-game'),
]
