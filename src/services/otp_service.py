import random
from datetime import datetime, timedelta
from django.utils import timezone
from src.models import OTP

class OTPService:
    @staticmethod
    def generate_otp(user, otp_type='login'):
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = timezone.now() + timedelta(minutes=5)
        
        OTP.objects.filter(user=user, otp_type=otp_type, is_used=False).update(is_used=True)
        
        otp = OTP.objects.create(
            user=user,
            code=code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        
        # TODO: Send OTP via email/SMS
        print(f"OTP for {user.email} ({otp_type}): {code}")
        
        return code
    
    @staticmethod
    def validate_otp(user, code, otp_type='login'):
        try:
            otp = OTP.objects.get(
                user=user,
                code=code,
                otp_type=otp_type,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            otp.is_used = True
            otp.save()
            return True
        except OTP.DoesNotExist:
            return False
