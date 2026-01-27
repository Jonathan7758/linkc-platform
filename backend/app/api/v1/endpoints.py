from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Welcome to ECIS Service Robot API"}

@router.get("/info")
async def info():
    return {
        "name": "ECIS Service Robot",
        "version": "1.0.0",
        "status": "running"
    }
