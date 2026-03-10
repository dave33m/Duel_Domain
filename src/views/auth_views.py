from rest_framework.decorators import api_view
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from src.services.auth_service import AuthService
from src.serializers import (

    SignupSerializer, SigninSerializer, VerifyOTPSerializer,
    SendOTPSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)

@swagger_auto_schema(method='post', request_body=SignupSerializer, tags=['auth'])
@api_view(['POST'])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.signup(**serializer.validated_data)
        return Response(result, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=SigninSerializer, tags=['auth'])
@api_view(['POST'])
def signin(request):
    serializer = SigninSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.signin(**serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

@swagger_auto_schema(method='post', request_body=VerifyOTPSerializer, tags=['auth'])
@api_view(['POST'])
def verify_otp(request):
    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.verify_otp(
            serializer.validated_data['user_id'],
            serializer.validated_data['otp'],
            serializer.validated_data.get('otp_type', 'login')
        )
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

@swagger_auto_schema(method='post', request_body=SendOTPSerializer, tags=['auth'])
@api_view(['POST'])
def send_otp(request):
    serializer = SendOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.send_otp(**serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=ForgotPasswordSerializer, tags=['auth'])
@api_view(['POST'])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.forgot_password(**serializer.validated_data)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=ResetPasswordSerializer, tags=['auth'])
@api_view(['POST'])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.reset_password(
            serializer.validated_data['user_id'],
            serializer.validated_data['otp'],
            serializer.validated_data['new_password']
        )
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='get', tags=['auth'])
@api_view(['GET'])
def get_all_users(request):
    try:
        users = AuthService.get_all_users()
        return Response({"users": users}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(method='delete', tags=['auth'])
@api_view(['DELETE'])
def delete_user(request, user_id):
    try:
        result = AuthService.delete_user(user_id)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)