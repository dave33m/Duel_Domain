from django.utils import timezone
from django.db import models
from src.models import Duel, Player, Game

class DuelService:
    @staticmethod
    def create_challenge(challenger_id, game_id, stake=0):
        try:
            challenger = Player.objects.get(id=challenger_id)
            game = Game.objects.get(id=game_id, is_active=True)
        except (Player.DoesNotExist, Game.DoesNotExist):
            raise ValueError("Invalid player or game")
        
        duel = Duel.objects.create(
            challenger=challenger,
            game=game,
            stake=stake,
            status='pending'
        )
        return duel
    
    @staticmethod
    def accept_challenge(duel_id, opponent_id):
        try:
            duel = Duel.objects.get(id=duel_id, status='pending')
            opponent = Player.objects.get(id=opponent_id)
        except (Duel.DoesNotExist, Player.DoesNotExist):
            raise ValueError("Invalid duel or player")
        
        if duel.challenger.id == opponent.id:
            raise ValueError("Cannot accept your own challenge")
        
        duel.opponent = opponent
        duel.status = 'accepted'
        duel.accepted_at = timezone.now()
        duel.save()
        return duel
    
    @staticmethod
    def submit_result(duel_id, player_id, score):
        try:
            duel = Duel.objects.get(id=duel_id, status='accepted')
            player = Player.objects.get(id=player_id)
        except (Duel.DoesNotExist, Player.DoesNotExist):
            raise ValueError("Invalid duel or player")
        
        if player.id == duel.challenger.id:
            duel.challenger_score = score
            duel.challenger_submitted = True
        elif player.id == duel.opponent.id:
            duel.opponent_score = score
            duel.opponent_submitted = True
        else:
            raise ValueError("Player not part of this duel")
        
        if duel.challenger_submitted and duel.opponent_submitted:
            if duel.challenger_score > duel.opponent_score:
                duel.winner = duel.challenger
                duel.challenger.wins += 1
                duel.opponent.losses += 1
            elif duel.opponent_score > duel.challenger_score:
                duel.winner = duel.opponent
                duel.opponent.wins += 1
                duel.challenger.losses += 1
            
            duel.status = 'completed'
            duel.completed_at = timezone.now()
            duel.challenger.save()
            duel.opponent.save()
        
        duel.save()
        return duel
    
    @staticmethod
    def get_player_duels(player_id):
        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            raise ValueError("Player not found")
        
        return Duel.objects.filter(
            models.Q(challenger=player) | models.Q(opponent=player)
        ).order_by('-created_at')
    
    @staticmethod
    def get_pending_challenges():
        return Duel.objects.filter(status='pending').order_by('-created_at')
