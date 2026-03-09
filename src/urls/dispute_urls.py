from django.urls import path
from src.views import dispute_views

urlpatterns = [
    path("flag/", dispute_views.flag_dispute, name='flag-dispute'),
    path("list/", dispute_views.get_disputed_duels, name='disputed-duels'),
    path("resolve/", dispute_views.resolve_dispute, name='resolve-dispute'),
    path("cancel/<uuid:duel_id>/", dispute_views.cancel_duel, name='cancel-duel'),
]
