from django.urls import path
from src.views import matchmaking_views

urlpatterns = [
    path("find/", matchmaking_views.find_opponents, name='find-opponents'),
    path("quick/", matchmaking_views.quick_match, name='quick-match'),
    path("recommended/", matchmaking_views.recommended_opponents, name='recommended-opponents'),
]
