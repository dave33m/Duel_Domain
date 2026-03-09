from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from src.services.game_service import GameService
from src.serializers import CreateGameSerializer, UpdateGameSerializer

@swagger_auto_schema(method='post', request_body=CreateGameSerializer, tags=['game'])
@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_game(request):
    serializer = CreateGameSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        game = GameService.create_game(**serializer.validated_data)
        return Response({
            "message": "Game created successfully",
            "game_id": str(game.id),
            "name": game.name,
            "platform": game.platform
        }, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('platform', openapi.IN_QUERY, type=openapi.TYPE_STRING, enum=['playstation', 'xbox', 'pc', 'mobile']),
        openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, default=True)
    ],
    tags=['game']
)
@api_view(['GET'])
def list_games(request):
    platform = request.GET.get('platform')
    is_active = request.GET.get('is_active', 'true').lower() == 'true'
    
    games = GameService.list_games(platform, is_active)
    return Response({
        "games": [{
            "id": str(g.id),
            "name": g.name,
            "platform": g.platform,
            "is_active": g.is_active
        } for g in games]
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('game_id', openapi.IN_PATH, type=openapi.TYPE_STRING, format='uuid')],
    tags=['game']
)
@api_view(['GET'])
def get_game(request, game_id):
    try:
        game = GameService.get_game(game_id)
        return Response({
            "id": str(game.id),
            "name": game.name,
            "platform": game.platform,
            "is_active": game.is_active,
            "created_at": game.created_at
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='put',
    request_body=UpdateGameSerializer,
    manual_parameters=[openapi.Parameter('game_id', openapi.IN_PATH, type=openapi.TYPE_STRING, format='uuid')],
    tags=['game']
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_game(request, game_id):
    serializer = UpdateGameSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        game = GameService.update_game(game_id, **serializer.validated_data)
        return Response({
            "message": "Game updated successfully",
            "id": str(game.id),
            "name": game.name,
            "platform": game.platform,
            "is_active": game.is_active
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='delete',
    manual_parameters=[openapi.Parameter('game_id', openapi.IN_PATH, type=openapi.TYPE_STRING, format='uuid')],
    tags=['game']
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_game(request, game_id):
    try:
        result = GameService.delete_game(game_id)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
