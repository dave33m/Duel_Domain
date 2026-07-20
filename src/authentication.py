from rest_framework import authentication, exceptions
from src.models import User
from src.services.jwt_service import JWTService


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode('utf-8')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != self.keyword.lower():
            return None

        try:
            payload = JWTService.decode_token(parts[1])
        except ValueError as e:
            raise exceptions.AuthenticationFailed(str(e))

        try:
            user = User.objects.get(id=payload['user_id'])
        except (User.DoesNotExist, KeyError, ValueError):
            raise exceptions.AuthenticationFailed('Invalid token')

        return (user, None)

    def authenticate_header(self, request):
        return self.keyword
