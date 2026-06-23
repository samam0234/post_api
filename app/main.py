# ============================================================
# 파일 위치: board_api/app/main.py
# 실행 방법: uvicorn app.main:app --reload
# ============================================================

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base, check_db_connection
from fastapi.middleware.cors import CORSMiddleware

from app import models   # noqa — Base가 Post 테이블을 인식하려면 반드시 import
from app.models import post_model
from app.routers.post_router import router as post_router

@asynccontextmanager
async def lifespan(app:FastAPI) :
    """
    FastAPI 객체가 생성될 때, 필요한 테이블이 자동 생성 되도록...
    """
    check_db_connection()
    Base.metadata.create_all(bind=engine)   # 없는 테이블 모두 생성. 있으면 pass
    # print(f"DB URL {engine.url}")
    # print(Base.metadata.tables)
    print("테이블 준비 OK")
    yield

app = FastAPI(
    title="게시판 API (MVC)",
    description="FastAPI + MariaDB + SQLAlchemy MVC 패턴",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정: 브라우저(프론트엔드)에서 API를 호출할 수 있게 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(post_router) # 분리된 router 모듈의 APIRouter 객체를 app에 포함

@app.get("/health", tags=["시스템"])
def health():
    return {"status": "ok"}