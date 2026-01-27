"""
ECIS Service Robot - API 主入口
================================
物业机器人服务平台 API
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as api_v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ECIS 物业机器人服务平台 API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {"name": settings.PROJECT_NAME, "version": settings.VERSION, "docs": "/docs", "api": settings.API_V1_PREFIX}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
