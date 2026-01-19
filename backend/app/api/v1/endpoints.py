from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Welcome to LinkC Platform API"}

@router.get("/info")
async def info():
    return {
        "name": "LinkC Platform",
        "version": "0.1.0",
        "status": "running"
    }
