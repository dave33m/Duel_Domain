from src.models import Player
from django.db.models import Q

class PlayerService:
    @staticmethod
    def get_profile(player_id):
        try:
            player = Player.objects.select_related('user').get(id=player_id)
            return {
                "id": str(player.id),
                "username": player.user.username,
                "email": player.user.email,
                "wins": player.wins,
                "losses": player.losses,
                "rating": player.rating,
                "win_rate": round((player.wins / (player.wins + player.losses) * 100), 2) if (player.wins + player.losses) > 0 else 0,
                "total_matches": player.wins + player.losses,
                "joined": player.created_at
            }
        except Player.DoesNotExist:
            raise ValueError("Player not found")
    
    @staticmethod
    def update_profile(player_id, username=None):
        try:
            player = Player.objects.select_related('user').get(id=player_id)
            if username:
                player.user.username = username
                player.user.save()
            return PlayerService.get_profile(player_id)
        except Player.DoesNotExist:
            raise ValueError("Player not found")
    
    @staticmethod
    def get_leaderboard(limit=50):
        players = Player.objects.select_related('user').order_by('-rating', '-wins')[:limit]
        return [{
            "rank": idx + 1,
            "id": str(p.id),
            "username": p.user.username,
            "rating": p.rating,
            "wins": p.wins,
            "losses": p.losses,
            "win_rate": round((p.wins / (p.wins + p.losses) * 100), 2) if (p.wins + p.losses) > 0 else 0
        } for idx, p in enumerate(players)]
    
    @staticmethod
    def search_players(query):
        players = Player.objects.select_related('user').filter(
            Q(user__username__icontains=query)
        )[:20]
        return [{
            "id": str(p.id),
            "username": p.user.username,
            "rating": p.rating,
            "wins": p.wins,
            "losses": p.losses
        } for p in players]


    @staticmethod
    def get_player_stats(player_id):
        try:
            player = Player.objects.get(id=player_id)
            total = player.wins + player.losses
            return {
                "wins": player.wins,
                "losses": player.losses,
                "total": total,
                "win_rate": round((player.wins / total * 100), 2) if total > 0 else 0
            }
        except Player.DoesNotExist:
            raise ValueError("Player not found")
