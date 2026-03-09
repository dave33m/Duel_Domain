from rest_framework import serializers

class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

class SigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class VerifyOTPSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    otp = serializers.CharField(max_length=6)
    otp_type = serializers.ChoiceField(choices=['login', 'password_reset'], default='login')

class SendOTPSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    otp_type = serializers.ChoiceField(choices=['login', 'password_reset'])

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
