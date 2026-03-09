from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    rating = models.IntegerField(default=1000)
    created_at = models.DateTimeField(auto_now_add=True)

class Duel(models.Model):
    player1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='duels_as_player1')
    player2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='duels_as_player2')
    winner = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_duels')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('active', 'Active'), ('completed', 'Completed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
