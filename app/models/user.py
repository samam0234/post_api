# ============================================================
# 파일 위치: board_api/app/models/user.py
# 유저 테이블 생성용
# ============================================================

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "user"

    # orm 내부에서 사용외는 unique한 값
    id              = Column(Integer, primary_key=True, autoincrement=True)
    # userId와 같은 의미의 username (보안쪽에서는 username = userId의 의미)
    username        = Column(String(50), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False)
    # 실명
    name            = Column(String(50), nullable=False)
    created_at      = Column(DateTime, default=datetime.now)