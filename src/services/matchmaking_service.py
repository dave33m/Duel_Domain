from src.models import Player, Game, Duel
from django.db.models import Q

class MatchmakingService:
    @staticmethod
    def find_opponents(player_id, game_id, rating_range=200):
        try:
            player = Player.objects.get(id=player_id)
            game = Game.objects.get(id=game_id, is_active=True)
        except (Player.DoesNotExist, Game.DoesNotExist):
            raise ValueError("Invalid player or game")
        
        min_rating = player.rating - rating_range
        max_rating = player.rating + rating_range
        
        opponents = Player.objects.filter(
            rating__gte=min_rating,
            rating__lte=max_rating
        ).exclude(id=player.id).select_related('user')[:20]
        
        return [{
            "id": str(p.id),
            "username": p.user.username,
            "rating": p.rating,
            "wins": p.wins,
            "losses": p.losses,
            "rating_diff": abs(p.rating - player.rating)
        } for p in opponents]
    
    @staticmethod
    def quick_match(player_id, game_id):
        try:
            player = Player.objects.get(id=player_id)
            game = Game.objects.get(id=game_id, is_active=True)
        except (Player.DoesNotExist, Game.DoesNotExist):
            raise ValueError("Invalid player or game")
        
        # Find pending challenges for this game
        pending_duels = Duel.objects.filter(
            game=game,
            status='pending',
            opponent__isnull=True
        ).exclude(challenger=player).select_related('challenger__user').order_by('-created_at')[:10]
        
        if not pending_duels:
            # Create a new challenge if no matches found
            duel = Duel.objects.create(
                challenger=player,
                game=game,
                status='pending'
            )
            return {
                "message": "No matches found. Challenge created.",
                "duel_id": str(duel.id),
                "status": "waiting"
            }
        
        # Return best match based on rating
        best_match = min(pending_duels, key=lambda d: abs(d.challenger.rating - player.rating))
        
        return {
            "message": "Match found",
            "duel_id": str(best_match.id),
            "opponent": best_match.challenger.user.username,
            "opponent_rating": best_match.challenger.rating,
            "status": "found"
        }
    
    @staticmethod
    def get_recommended_opponents(player_id, limit=10):
        try:
            player = Player.objects.get(id=player_id)
        except Player.DoesNotExist:
            raise ValueError("Player not found")
        
        # Find players with similar rating
        opponents = Player.objects.filter(
            rating__gte=player.rating - 100,
            rating__lte=player.rating + 100
        ).exclude(id=player.id).select_related('user').order_by('?')[:limit]
        
        return [{
            "id": str(p.id),
            "username": p.user.username,
            "rating": p.rating,
            "wins": p.wins,
            "losses": p.losses
        } for p in opponents]
