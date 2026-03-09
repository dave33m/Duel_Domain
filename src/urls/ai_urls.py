from django.urls import path
from src.views import ai_views

urlpatterns = [
    path("chat/", ai_views.chat_assistant, name='chat-assistant'),
    path("validate-screenshot/", ai_views.validate_screenshot, name='validate-screenshot'),
    path("performance/", ai_views.performance_analysis, name='performance-analysis'),
]
