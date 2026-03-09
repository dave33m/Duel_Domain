from django.urls import path
from . import views

urlpatterns = [
    path("auth/signup/", views.signup),
    path("auth/signin/", views.signin),
]