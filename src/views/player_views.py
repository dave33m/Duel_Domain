from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from src.services.player_service import PlayerService
from src.serializers import UpdateProfileSerializer

@swagger_auto_schema(method='get', tags=['player'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_profile(request):
    try:
        player = request.user.player
        profile = PlayerService.get_profile(player.id)
        return Response(profile, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('player_id', openapi.IN_PATH, type=openapi.TYPE_STRING, format='uuid')],
    tags=['player']
)
@api_view(['GET'])
def get_profile(request, player_id):
    try:
        profile = PlayerService.get_profile(player_id)
        return Response(profile, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(method='put', request_body=UpdateProfileSerializer, tags=['player'])
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UpdateProfileSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        player = request.user.player
        profile = PlayerService.update_profile(player.id, **serializer.validated_data)
        return Response(profile, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('limit', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=50)],
    tags=['player']
)
@api_view(['GET'])
def leaderboard(request):
    limit = int(request.GET.get('limit', 50))
    players = PlayerService.get_leaderboard(limit)
    return Response({"leaderboard": players}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('q', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
    tags=['player']
)
@api_view(['GET'])
def search_players(request):
    query = request.GET.get('q', '')
    if not query:
        return Response({"error": "Query parameter required"}, status=status.HTTP_400_BAD_REQUEST)
    
    players = PlayerService.search_players(query)
    return Response({"players": players}, status=status.HTTP_200_OK)

@swagger_auto_schema(method='get', tags=['player'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_stats(request):
    try:
        player = request.user.player
        stats = PlayerService.get_player_stats(player.id)
        return Response(stats, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
