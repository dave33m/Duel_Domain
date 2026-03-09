from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from src.services.auth_service import AuthService

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email', 'username', 'password'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
    responses={201: openapi.Response('User created', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
    ))},
    tags=['auth']
)
@api_view(['POST'])
def signup(request):
    email = request.data.get('email')
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not all([email, username, password]):
        return Response({"error": "All fields required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.signup(email, username, password)
        return Response(result, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email', 'password'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
    responses={200: openapi.Response('OTP sent', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING),
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        }
    ))},
    tags=['auth']
)
@api_view(['POST'])
def signin(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not all([email, password]):
        return Response({"error": "Email and password required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.signin(email, password)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['user_id', 'otp'],
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'otp': openapi.Schema(type=openapi.TYPE_STRING),
            'otp_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['login', 'password_reset'], default='login'),
        },
    ),
    responses={200: openapi.Response('Verification successful', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'token': openapi.Schema(type=openapi.TYPE_STRING),
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ))},
    tags=['auth']
)
@api_view(['POST'])
def verify_otp(request):
    user_id = request.data.get('user_id')
    otp = request.data.get('otp')
    otp_type = request.data.get('otp_type', 'login')
    
    if not all([user_id, otp]):
        return Response({"error": "User ID and OTP required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.verify_otp(user_id, otp, otp_type)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['user_id', 'otp_type'],
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'otp_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['login', 'password_reset']),
        },
    ),
    responses={200: openapi.Response('OTP sent', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
    ))},
    tags=['auth']
)
@api_view(['POST'])
def send_otp(request):
    user_id = request.data.get('user_id')
    otp_type = request.data.get('otp_type')
    
    if not all([user_id, otp_type]):
        return Response({"error": "User ID and OTP type required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.send_otp(user_id, otp_type)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={'email': openapi.Schema(type=openapi.TYPE_STRING)},
    ),
    responses={200: openapi.Response('OTP sent', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'message': openapi.Schema(type=openapi.TYPE_STRING),
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        }
    ))},
    tags=['auth']
)
@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')
    
    if not email:
        return Response({"error": "Email required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.forgot_password(email)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['user_id', 'otp', 'new_password'],
        properties={
            'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'otp': openapi.Schema(type=openapi.TYPE_STRING),
            'new_password': openapi.Schema(type=openapi.TYPE_STRING),
        },
    ),
    responses={200: openapi.Response('Password reset', openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={'message': openapi.Schema(type=openapi.TYPE_STRING)}
    ))},
    tags=['auth']
)
@api_view(['POST'])
def reset_password(request):
    user_id = request.data.get('user_id')
    otp = request.data.get('otp')
    new_password = request.data.get('new_password')
    
    if not all([user_id, otp, new_password]):
        return Response({"error": "All fields required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = AuthService.reset_password(user_id, otp, new_password)
        return Response(result, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
