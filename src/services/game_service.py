from src.models import Game

class GameService:
    @staticmethod
    def create_game(name, platform):
        if Game.objects.filter(name=name, platform=platform).exists():
            raise ValueError("Game already exists for this platform")
        
        game = Game.objects.create(name=name, platform=platform)
        return game
    
    @staticmethod
    def list_games(platform=None, is_active=True):
        queryset = Game.objects.filter(is_active=is_active)
        if platform:
            queryset = queryset.filter(platform=platform)
        return queryset.order_by('name')
    
    @staticmethod
    def get_game(game_id):
        try:
            return Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            raise ValueError("Game not found")
    
    @staticmethod
    def update_game(game_id, name=None, platform=None, is_active=None):
        try:
            game = Game.objects.get(id=game_id)
            if name:
                game.name = name
            if platform:
                game.platform = platform
            if is_active is not None:
                game.is_active = is_active
            game.save()
            return game
        except Game.DoesNotExist:
            raise ValueError("Game not found")
    
    @staticmethod
    def delete_game(game_id):
        try:
            game = Game.objects.get(id=game_id)
            game.is_active = False
            game.save()
            return {"message": "Game deactivated successfully"}
        except Game.DoesNotExist:
            raise ValueError("Game not found")
