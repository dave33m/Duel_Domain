from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from src.services.duel_service import DuelService
from src.serializers import CreateChallengeSerializer, AcceptChallengeSerializer, SubmitResultSerializer

@swagger_auto_schema(method='post', request_body=CreateChallengeSerializer, tags=['duel'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_challenge(request):
    serializer = CreateChallengeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        player = request.user.player
        duel = DuelService.create_challenge(
            player.id,
            serializer.validated_data['game_id'],
            serializer.validated_data.get('stake', 0)
        )
        return Response({
            "message": "Challenge created successfully",
            "duel_id": str(duel.id)
        }, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=AcceptChallengeSerializer, tags=['duel'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_challenge(request):
    serializer = AcceptChallengeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        player = request.user.player
        duel = DuelService.accept_challenge(
            serializer.validated_data['duel_id'],
            player.id
        )
        return Response({
            "message": "Challenge accepted successfully",
            "duel_id": str(duel.id)
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=SubmitResultSerializer, tags=['duel'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_result(request):
    serializer = SubmitResultSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        player = request.user.player
        duel = DuelService.submit_result(
            serializer.validated_data['duel_id'],
            player.id,
            serializer.validated_data['score']
        )
        return Response({
            "message": "Result submitted successfully",
            "status": duel.status
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='get', tags=['duel'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_duels(request):
    try:
        player = request.user.player
        duels = DuelService.get_player_duels(player.id)
        return Response({
            "duels": [{
                "id": str(d.id),
                "game": d.game.name,
                "status": d.status,
                "created_at": d.created_at
            } for d in duels]
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='get', tags=['duel'])
@api_view(['GET'])
def pending_challenges(request):
    duels = DuelService.get_pending_challenges()
    return Response({
        "challenges": [{
            "id": str(d.id),
            "game": d.game.name,
            "challenger": d.challenger.user.username,
            "stake": str(d.stake),
            "created_at": d.created_at
        } for d in duels]
    }, status=status.HTTP_200_OK)
