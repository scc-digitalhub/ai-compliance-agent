from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["system"])


@router.get("/health", summary="Liveness")
async def health():
    return {"status": "ok"}


@router.get("/ready", summary="Readiness: agents built and OKF bundle loaded")
async def ready(request: Request):
    registry = getattr(request.app.state, "registry", None)
    if registry is None or not registry.bundle.concepts:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready", "okf_version": registry.bundle.version, "concepts": len(registry.bundle.concepts)}
