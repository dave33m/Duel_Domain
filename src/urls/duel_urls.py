from django.urls import path
from src.views import duel_views

urlpatterns = [
    path("create/", duel_views.create_challenge, name='create-challenge'),
    path("accept/", duel_views.accept_challenge, name='accept-challenge'),
    path("submit-result/", duel_views.submit_result, name='submit-result'),
    path("my-duels/", duel_views.my_duels, name='my-duels'),
    path("pending/", duel_views.pending_challenges, name='pending-challenges'),
]
