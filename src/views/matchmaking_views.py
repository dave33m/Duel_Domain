from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from src.services.matchmaking_service import MatchmakingService
from src.serializers import FindOpponentsSerializer, QuickMatchSerializer

@swagger_auto_schema(method='post', request_body=FindOpponentsSerializer, tags=['matchmaking'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def find_opponents(request):
    serializer = FindOpponentsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        player = request.user.player
        opponents = MatchmakingService.find_opponents(
            player.id,
            serializer.validated_data['game_id'],
            serializer.validated_data.get('rating_range', 200)
        )
        return Response({"opponents": opponents}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=QuickMatchSerializer, tags=['matchmaking'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_match(request):
    serializer = QuickMatchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        player = request.user.player
        result = MatchmakingService.quick_match(
            player.id,
            serializer.validated_data['game_id']
        )
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('limit', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=10)],
    tags=['matchmaking']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_opponents(request):
    try:
        player = request.user.player
        limit = int(request.GET.get('limit', 10))
        opponents = MatchmakingService.get_recommended_opponents(player.id, limit)
        return Response({"recommended": opponents}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
