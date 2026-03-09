from django.utils import timezone
from src.models import Duel, Player

class DisputeService:
    @staticmethod
    def flag_dispute(duel_id, player_id, reason):
        try:
            duel = Duel.objects.get(id=duel_id)
            player = Player.objects.get(id=player_id)
        except (Duel.DoesNotExist, Player.DoesNotExist):
            raise ValueError("Invalid duel or player")
        
        if player.id not in [duel.challenger.id, duel.opponent.id]:
            raise ValueError("Player not part of this duel")
        
        if duel.status != 'completed':
            raise ValueError("Can only dispute completed duels")
        
        duel.status = 'disputed'
        duel.save()
        return {"message": "Duel flagged for dispute resolution"}
    
    @staticmethod
    def get_disputed_duels():
        duels = Duel.objects.filter(status='disputed').select_related(
            'game', 'challenger__user', 'opponent__user', 'winner__user'
        ).order_by('-created_at')
        
        return [{
            "id": str(d.id),
            "game": d.game.name,
            "challenger": d.challenger.user.username,
            "opponent": d.opponent.user.username if d.opponent else None,
            "challenger_score": d.challenger_score,
            "opponent_score": d.opponent_score,
            "winner": d.winner.user.username if d.winner else None,
            "created_at": d.created_at,
            "completed_at": d.completed_at
        } for d in duels]
    
    @staticmethod
    def resolve_dispute(duel_id, winner_id):
        try:
            duel = Duel.objects.get(id=duel_id, status='disputed')
            winner = Player.objects.get(id=winner_id)
        except (Duel.DoesNotExist, Player.DoesNotExist):
            raise ValueError("Invalid duel or player")
        
        if winner.id not in [duel.challenger.id, duel.opponent.id]:
            raise ValueError("Winner must be one of the duel participants")
        
        # Revert previous stats
        if duel.winner:
            if duel.winner.id == duel.challenger.id:
                duel.challenger.wins -= 1
                duel.opponent.losses -= 1
            else:
                duel.opponent.wins -= 1
                duel.challenger.losses -= 1
        
        # Apply new winner
        duel.winner = winner
        if winner.id == duel.challenger.id:
            duel.challenger.wins += 1
            duel.opponent.losses += 1
        else:
            duel.opponent.wins += 1
            duel.challenger.losses += 1
        
        duel.status = 'completed'
        duel.save()
        duel.challenger.save()
        duel.opponent.save()
        
        return {"message": "Dispute resolved successfully"}
    
    @staticmethod
    def cancel_duel(duel_id, admin=False):
        try:
            duel = Duel.objects.get(id=duel_id)
        except Duel.DoesNotExist:
            raise ValueError("Duel not found")
        
        if not admin and duel.status not in ['pending', 'accepted']:
            raise ValueError("Can only cancel pending or accepted duels")
        
        duel.status = 'cancelled'
        duel.save()
        return {"message": "Duel cancelled successfully"}
