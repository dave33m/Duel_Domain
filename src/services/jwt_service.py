import jwt
from datetime import datetime, timedelta
from django.conf import settings

class JWTService:
    SECRET_KEY = settings.SECRET_KEY
    
    @staticmethod
    def generate_token(user_id, username, email):
        payload = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWTService.SECRET_KEY, algorithm='HS256')
    
    @staticmethod
    def decode_token(token):
        try:
            return jwt.decode(token, JWTService.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
