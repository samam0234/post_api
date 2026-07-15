# ============================================================
# 파일 위치: board_api/app/repositories/user_repository.py
# 역할: User 테이블 접근만 담당합니다.
# ============================================================

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.models.user import User

class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> Optional[User]:
        """
        id(username)로 회원 정보 검색
        """
        return self.db.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        orm 내부에서 숫자로 된 unique한 id로 조회하는 함수
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, username: str, hashed_password: str, name: str) -> User:
        """
        회원가입
        ⚠️ hashed_password는 이미 해싱된 값을 받습니다.
        해싱 자체는 Service가 app.auth.jwt.hash_password()로 미리 처리합니다.
        """
        user = User(
            username=username, hashed_password=hashed_password,
            name=name, created_at=datetime.now(),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user