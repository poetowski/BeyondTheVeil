from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.v1 import api_router
from app.core.config import settings

app = FastAPI(title="Beyond the Veil")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Deployed as a single service (see render.yaml): the frontend's built
# assets live alongside the backend, so this process serves both instead
# of running two separate services. Any path that isn't an API route or a
# real built file falls back to index.html so React Router can take over
# client-side. A no-op in local dev, where frontend/dist doesn't exist
# (the frontend runs its own Vite dev server instead).
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST / "index.html")
