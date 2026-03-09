from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from src.services.ai_service import AIService
from src.serializers import ChatAssistantSerializer, ValidateScreenshotSerializer

@swagger_auto_schema(method='post', request_body=ChatAssistantSerializer, tags=['ai'])
@api_view(['POST'])
def chat_assistant(request):
    """
    Airee - AI chat assistant for Duel Domain
    """
    serializer = ChatAssistantSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    message = serializer.validated_data['message']
    context = {}
    
    if request.user.is_authenticated:
        context['user_id'] = str(request.user.id)
        context['username'] = request.user.username
    
    response = AIService.chat_assistant(message, context)
    return Response({
        "airee": response,
        "message": message
    }, status=status.HTTP_200_OK)

@swagger_auto_schema(method='post', request_body=ValidateScreenshotSerializer, tags=['ai'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_screenshot(request):
    """
    AI-powered screenshot validation using OCR
    """
    serializer = ValidateScreenshotSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    result = AIService.validate_screenshot(serializer.validated_data['image_url'])
    return Response(result, status=status.HTTP_200_OK)

@swagger_auto_schema(method='get', tags=['ai'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_analysis(request):
    """
    AI-powered performance analysis
    """
    try:
        player = request.user.player
        # Get recent duel history (placeholder)
        player_history = []
        
        analysis = AIService.analyze_performance(player_history)
        return Response(analysis, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
