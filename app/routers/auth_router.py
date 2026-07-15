# ============================================================
# 파일 위치: board_api/app/routers/auth_router.py
# ============================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate, UserInfo

# main.py 의 FastAPI 에 등록할 분리된 라우터 모듈
auth_router = APIRouter(prefix="/auth", tags=["인증"])

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

@auth_router.post("/register", response_model=UserInfo, status_code=201, summary="회원가입")
def register(
    data: UserCreate,
    service: AuthService = Depends(get_auth_service)
) :
    return service.register(data)