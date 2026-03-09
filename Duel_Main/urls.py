"""
URL configuration for Duel_Main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Duel Domain API",
        default_version='v1',
        description="API documentation",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path("auth/", include(("src.urls.auth_urls", "auth"), namespace="auth")),
    path("duel/", include(("src.urls.duel_urls", "duel"), namespace="duel")),
    path("player/", include(("src.urls.player_urls", "player"), namespace="player")),
    path("game/", include(("src.urls.game_urls", "game"), namespace="game")),
    path("evidence/", include(("src.urls.evidence_urls", "evidence"), namespace="evidence")),
    path("dispute/", include(("src.urls.dispute_urls", "dispute"), namespace="dispute")),
    path("matchmaking/", include(("src.urls.matchmaking_urls", "matchmaking"), namespace="matchmaking")),
    path("ai/", include(("src.urls.ai_urls", "ai"), namespace="ai")),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
