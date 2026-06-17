# ============================================================
# 파일 위치: board_api/app/main.py
# 실행 방법: uvicorn app.main:app --reload
# ============================================================

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import engine, Base, check_db_connection
from app import models   # noqa — Base가 Post 테이블을 인식하려면 반드시 import
from app.models import post_model

@asynccontextmanager
async def lifespan(app:FastAPI) :
    """
    FastAPI 객체가 생성될 때, 필요한 테이블이 자동 생성 되도록...
    """
    check_db_connection()
    Base.metadata.create_all(bind=engine)   # 없는 테이블 모두 생성. 있으면 pass
    print(Base.metadata.tables)
    print("테이블 준비 OK")
    yield

app = FastAPI(
    title="게시판 API (MVC)",
    description="FastAPI + MariaDB + SQLAlchemy MVC 패턴",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health", tags=["시스템"])
def health():
    return {"status": "ok"}