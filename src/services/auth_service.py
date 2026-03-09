from django.contrib.auth.models import User
from src.models import Player
from src.services.otp_service import OTPService
from src.services.jwt_service import JWTService

class AuthService:
    @staticmethod
    def signup(email, username, password):
        if User.objects.filter(email=email).exists():
            raise ValueError("Email already exists")
        if User.objects.filter(username=username).exists():
            raise ValueError("Username already exists")
        
        user = User.objects.create_user(username=username, email=email, password=password)
        Player.objects.create(user=user)
        return {"message": "Sign up successful, welcome to Duel Domain"}
    
    @staticmethod
    def signin(email, password):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("Invalid credentials")
        
        if not user.check_password(password):
            raise ValueError("Invalid credentials")
        
        OTPService.generate_otp(user, 'login')
        return {"message": "OTP sent successfully", "user_id": user.id}
    
    @staticmethod
    def verify_otp(user_id, code, otp_type='login'):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError("User not found")
        
        if not OTPService.validate_otp(user, code, otp_type):
            raise ValueError("Invalid or expired OTP")
        
        token = JWTService.generate_token(user.id, user.username, user.email)
        return {"token": token, "username": user.username, "email": user.email}
    
    @staticmethod
    def send_otp(user_id, otp_type):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError("User not found")
        
        OTPService.generate_otp(user, otp_type)
        return {"message": "OTP sent successfully"}
    
    @staticmethod
    def forgot_password(email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValueError("Email not found")
        
        OTPService.generate_otp(user, 'password_reset')
        return {"message": "Password reset OTP sent successfully", "user_id": user.id}
    
    @staticmethod
    def reset_password(user_id, otp, new_password):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError("User not found")
        
        if not OTPService.validate_otp(user, otp, 'password_reset'):
            raise ValueError("Invalid or expired OTP")
        
        user.set_password(new_password)
        user.save()
        return {"message": "Password reset successful"}
