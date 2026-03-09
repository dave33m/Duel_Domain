from django.urls import path
from src.views import evidence_views

urlpatterns = [
    path("upload/", evidence_views.upload_evidence, name='upload-evidence'),
    path("duel/<uuid:duel_id>/", evidence_views.get_duel_evidence, name='get-duel-evidence'),
    path("<uuid:evidence_id>/delete/", evidence_views.delete_evidence, name='delete-evidence'),
]
