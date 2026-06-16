# ============================================================
# 파일 위치: board_api/app/models/post.py
# 역할: DB 테이블 구조만 정의합니다. 쿼리 로직은 여기 없습니다.
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class Post(Base):
    __tablename__ = "post"

    id         = Column(Integer, primary_key=True, autoincrement=True, comment="게시글 번호 PK")
    title      = Column(String(200), nullable=False, comment="게시글 제목")
    content    = Column(Text, nullable=False, comment="게시글 본문")
    author     = Column(String(50), nullable=False, comment="작성자")
    view_count = Column(Integer, default=0, comment="조회수")
    created_at = Column(DateTime, default=datetime.now, comment="작성 시각")
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,   # UPDATE 실행 시 자동으로 현재 시각 갱신
        comment="수정 시각"
    )