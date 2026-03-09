from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from src.services.evidence_service import EvidenceService
from src.serializers import UploadEvidenceSerializer

@swagger_auto_schema(method='post', request_body=UploadEvidenceSerializer, tags=['evidence'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_evidence(request):
    serializer = UploadEvidenceSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        player = request.user.player
        evidence = EvidenceService.upload_evidence(
            serializer.validated_data['duel_id'],
            player.id,
            serializer.validated_data['evidence_url']
        )
        return Response({
            "message": "Evidence uploaded successfully",
            "evidence_id": str(evidence.id)
        }, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('duel_id', openapi.IN_PATH, type=openapi.TYPE_STRING, format='uuid')],
    tags=['evidence']
)
@api_view(['GET'])
def get_duel_evidence(request, duel_id):
    try:
        evidence = EvidenceService.get_duel_evidence(duel_id)
        return Response({"evidence": evidence}, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='delete',
    manual_parameters=[openapi.Parameter('evidence_id', openapi.IN_PATH, type=openapi.TYPE_STRING, format='uuid')],
    tags=['evidence']
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_evidence(request, evidence_id):
    try:
        player = request.user.player
        result = EvidenceService.delete_evidence(evidence_id, player.id)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
