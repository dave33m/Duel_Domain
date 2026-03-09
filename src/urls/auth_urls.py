from django.urls import path
from src.views import auth_views

urlpatterns = [
    path("signup/", auth_views.signup, name='signup'),
    path("signin/", auth_views.signin, name='signin'),
    path("verify-otp/", auth_views.verify_otp, name='verify-otp'),
    path("send-otp/", auth_views.send_otp, name='send-otp'),
    path("forgot-password/", auth_views.forgot_password, name='forgot-password'),
    path("reset-password/", auth_views.reset_password, name='reset-password'),
]
