from src.models import MatchEvidence, Duel, Player

class EvidenceService:
    @staticmethod
    def upload_evidence(duel_id, player_id, evidence_url):
        try:
            duel = Duel.objects.get(id=duel_id)
            player = Player.objects.get(id=player_id)
        except (Duel.DoesNotExist, Player.DoesNotExist):
            raise ValueError("Invalid duel or player")
        
        if player.id not in [duel.challenger.id, duel.opponent.id]:
            raise ValueError("Player not part of this duel")
        
        evidence = MatchEvidence.objects.create(
            duel=duel,
            submitted_by=player,
            evidence_url=evidence_url
        )
        return evidence
    
    @staticmethod
    def get_duel_evidence(duel_id):
        try:
            duel = Duel.objects.get(id=duel_id)
        except Duel.DoesNotExist:
            raise ValueError("Duel not found")
        
        evidence = MatchEvidence.objects.filter(duel=duel).select_related('submitted_by__user')
        return [{
            "id": str(e.id),
            "submitted_by": e.submitted_by.user.username,
            "evidence_url": e.evidence_url,
            "created_at": e.created_at
        } for e in evidence]
    
    @staticmethod
    def delete_evidence(evidence_id, player_id):
        try:
            evidence = MatchEvidence.objects.get(id=evidence_id)
            player = Player.objects.get(id=player_id)
        except (MatchEvidence.DoesNotExist, Player.DoesNotExist):
            raise ValueError("Invalid evidence or player")
        
        if evidence.submitted_by.id != player.id:
            raise ValueError("Cannot delete evidence submitted by another player")
        
        evidence.delete()
        return {"message": "Evidence deleted successfully"}
