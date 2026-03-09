from django.db import models
from django.contrib.auth.models import User
import uuid

class Player(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    rating = models.IntegerField(default=1000)
    created_at = models.DateTimeField(auto_now_add=True)

class Game(models.Model):
    PLATFORM_CHOICES = [
        ('playstation', 'PlayStation'),
        ('xbox', 'Xbox'),
        ('pc', 'PC'),
        ('mobile', 'Mobile'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Duel(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    challenger = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='challenges_created')
    opponent = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='challenges_received', null=True, blank=True)
    winner = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='duels_won')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stake = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    challenger_score = models.IntegerField(null=True, blank=True)
    opponent_score = models.IntegerField(null=True, blank=True)
    challenger_submitted = models.BooleanField(default=False)
    opponent_submitted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class MatchEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    duel = models.ForeignKey(Duel, on_delete=models.CASCADE, related_name='evidence')
    submitted_by = models.ForeignKey(Player, on_delete=models.CASCADE)
    evidence_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

class OTP(models.Model):
    OTP_TYPE_CHOICES = [
        ('login', 'Login'),
        ('password_reset', 'Password Reset'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES, default='login')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
