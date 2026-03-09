from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from src.services.dispute_service import DisputeService
from src.serializers import FlagDisputeSerializer, ResolveDisputeSerializer

@swagger_auto_schema(method='post', request_body=FlagDisputeSerializer, tags=['dispute'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flag_dispute(request):
    serializer = FlagDisputeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        player = request.user.player
        result = DisputeService.flag_dispute(
            serializer.validated_data['duel_id'],
            player.id,
            serializer.validated_data['reason']
        )
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='get', tags=['dispute'])
@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_disputed_duels(request):
    duels = DisputeService.get_disputed_duels()
    return Response({"disputed_duels": duels}, status=status.HTTP_200_OK)

@swagger_auto_schema(method='post', request_body=ResolveDisputeSerializer, tags=['dispute'])
@api_view(['POST'])
@permission_classes([IsAdminUser])
def resolve_dispute(request):
    serializer = ResolveDisputeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = DisputeService.resolve_dispute(
            serializer.validated_data['duel_id'],
            serializer.validated_data['winner_id']
        )
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    manual_parameters=[openapi.Parameter('duel_id', openapi.IN_PATH, type=openapi.TYPE_STRING, format='uuid')],
    tags=['dispute']
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def cancel_duel(request, duel_id):
    try:
        result = DisputeService.cancel_duel(duel_id, admin=True)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
