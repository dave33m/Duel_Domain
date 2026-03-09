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

class CreateChallengeSerializer(serializers.Serializer):
    game_id = serializers.UUIDField()
    stake = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)

class AcceptChallengeSerializer(serializers.Serializer):
    duel_id = serializers.UUIDField()

class SubmitResultSerializer(serializers.Serializer):
    duel_id = serializers.UUIDField()
    score = serializers.IntegerField()

class UpdateProfileSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False)

class CreateGameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    platform = serializers.ChoiceField(choices=['playstation', 'xbox', 'pc', 'mobile'])

class UpdateGameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False)
    platform = serializers.ChoiceField(choices=['playstation', 'xbox', 'pc', 'mobile'], required=False)
    is_active = serializers.BooleanField(required=False)

class UploadEvidenceSerializer(serializers.Serializer):
    duel_id = serializers.UUIDField()
    evidence_url = serializers.URLField()

class FlagDisputeSerializer(serializers.Serializer):
    duel_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=500)

class ResolveDisputeSerializer(serializers.Serializer):
    duel_id = serializers.UUIDField()
    winner_id = serializers.UUIDField()

class FindOpponentsSerializer(serializers.Serializer):
    game_id = serializers.UUIDField()
    rating_range = serializers.IntegerField(default=200, required=False)

class QuickMatchSerializer(serializers.Serializer):
    game_id = serializers.UUIDField()

class ChatAssistantSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=500)

class ValidateScreenshotSerializer(serializers.Serializer):
    image_url = serializers.URLField()
