# ============================================================
# 파일 위치: board_api/app/services/auth_service.py
# ============================================================

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.auth.jwt import hash_password
from app.schemas.auth import UserCreate, UserInfo

class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
        
    def register(self, data: UserCreate) -> UserInfo:
        """
        회원가입.
        1. 아이디 중복 검사 (Repository 조회)
        2. 비밀번호 해싱 (app.auth.jwt)
        3. 저장 (Repository)
        """
        if self.user_repo.get_by_username(data.username):
            raise HTTPException(status_code=400, detail="이미 사용 중인 아이디입니다.")

        user = self.user_repo.create(
            username=data.username,
            hashed_password=hash_password(data.password),
            name=data.name,
        )
        return UserInfo.model_validate(user)