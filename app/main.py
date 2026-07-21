from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.limiter import limiter
from app.routers import ai, auth, dispute, duel, evidence, game, matchmaking, player

app = FastAPI(
    title="Duel Domain API",
    description="API documentation",
    version="v1",
    docs_url="/swagger/",
    redoc_url="/redoc/",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(player.router)
app.include_router(game.router)
app.include_router(duel.router)
app.include_router(matchmaking.router)
app.include_router(evidence.router)
app.include_router(dispute.router)
app.include_router(ai.router)


@app.get("/health/")
def health():
    return {"status": "ok"}
