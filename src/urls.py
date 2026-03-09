from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name='signup'),
    path("signin/", views.signin, name='signin'),
    path("verify-otp/", views.verify_otp, name='verify-otp'),
    path("send-otp/", views.send_otp, name='send-otp'),
    path("forgot-password/", views.forgot_password, name='forgot-password'),
    path("reset-password/", views.reset_password, name='reset-password'),
]