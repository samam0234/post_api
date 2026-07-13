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

# ============================================================
# ↓↓↓ 여기부터 MCP(Model Context Protocol) 서버 마운트 코드 ↓↓↓
# ------------------------------------------------------------
# fastapi-mcp는 위에서 만든 FastAPI 앱(app)을 그대로 읽어서
# 각 엔드포인트를 Claude 같은 LLM이 호출 가능한 "도구(tool)"로
# 자동 변환해줍니다. 반드시 include_router 이후에 위치해야 합니다.
# ============================================================
from fastapi_mcp import FastApiMCP

mcp = FastApiMCP(
    app, # 도구로 변환할 MCP 앱
    name="게시판 API", # Claude (LLM)에 표시될 MCP 서버 이름
    description="게시판 등록/조회/목록/수정/삭제를 수행하는 MCP 도구",
    include_operations=[
        "create_post",
        "get_post",
        "list_posts",
        "update_post",
        "delete_post",
    ]
    # with-files, with-stat, /health 등은 include_operations에 없으므로
    # 자동으로 MCP 도구 목록에서 제외됩니다.
)

#  /mcp 경로에 MCP 서버를 "마운트"합니다.
# - Streamable HTTP transport를 사용하며, 별도 프로세스 없이
#   지금 이 FastAPI 앱(uvicorn 프로세스) 안에서 함께 실행됩니다.
# - 이후 http://localhost:8000/mcp 로 MCP 클라이언트가 접속할 수 있습니다.
mcp.mount_http()