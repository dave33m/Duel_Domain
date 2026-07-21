from typing import Any


class AIService:
    """
    AI service for Duel Domain platform.
    Placeholder logic pending real AI/OCR integration.
    """

    @staticmethod
    def chat_assistant(user_message: str, context: dict[str, Any] | None = None) -> str:
        responses = {
            "how to create duel": "To create a duel, go to /duel/create/ and provide game_id and optional stake amount.",
            "how to find opponent": "Use /matchmaking/find/ to find opponents by rating, or /matchmaking/quick/ for instant matching.",
            "how to submit result": "After completing your match, use /duel/submit-result/ with your duel_id and score.",
            "what is my rating": "Check your profile at /player/me/ to see your current rating and stats.",
        }

        message_lower = user_message.lower()
        for key, response in responses.items():
            if key in message_lower:
                return response

        return "I'm Airee, your Duel Domain assistant! Ask me about creating duels, finding opponents, or checking your stats."

    @staticmethod
    def validate_screenshot(image_url: str) -> dict[str, Any]:
        # TODO: Integrate with OCR service (AWS Textract, Google Vision, etc.)
        return {
            "valid": True,
            "confidence": 0.85,
            "detected_scores": {"player1": None, "player2": None},
            "message": "Screenshot validation pending AI integration",
        }

    @staticmethod
    def detect_fraud(player_id: str, recent_duels: list) -> dict[str, Any]:
        if len(recent_duels) > 10:
            win_rate = sum(1 for d in recent_duels if d.get("won")) / len(recent_duels)
            if win_rate > 0.95:
                return {
                    "suspicious": True,
                    "confidence": 0.75,
                    "reason": "Unusually high win rate",
                    "recommendation": "Manual review recommended",
                }

        return {"suspicious": False, "confidence": 0.9, "message": "No suspicious activity detected"}

    @staticmethod
    def recommend_strategy(player_stats: dict[str, Any], opponent_stats: dict[str, Any]) -> str:
        player_rating = player_stats.get("rating", 1000)
        opponent_rating = opponent_stats.get("rating", 1000)

        if opponent_rating > player_rating + 100:
            return "Your opponent has a higher rating. Focus on defensive play and capitalize on their mistakes."
        elif player_rating > opponent_rating + 100:
            return "You have the rating advantage. Play aggressively and maintain pressure."
        else:
            return "Evenly matched! Stay focused and adapt to your opponent's playstyle."

    @staticmethod
    def analyze_performance(player_history: list) -> dict[str, Any]:
        if not player_history:
            return {"message": "Not enough data for analysis"}

        recent_wins = sum(1 for d in player_history[-10:] if d.get("won"))

        return {
            "recent_form": "good" if recent_wins >= 6 else "average" if recent_wins >= 4 else "poor",
            "win_streak": recent_wins,
            "recommendation": "Keep up the momentum!" if recent_wins >= 6 else "Practice more to improve your skills.",
            "insights": "AI-powered insights coming soon",
        }
