from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from src.models import Player

class AuthService:
    @staticmethod
    def signup(email, username, password):
        if User.objects.filter(email=email).exists():
            raise ValueError("Email already exists")
        if User.objects.filter(username=username).exists():
            raise ValueError("Username already exists")
        
        user = User.objects.create_user(username=username, email=email, password=password)
        Player.objects.create(user=user)
        token = Token.objects.create(user=user)
        return {"user": user, "token": token.key}
    
    @staticmethod
    def signin(email, password):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("Invalid credentials")
        
        if not user.check_password(password):
            raise ValueError("Invalid credentials")
        
        token, _ = Token.objects.get_or_create(user=user)
        return {"user": user, "token": token.key}
