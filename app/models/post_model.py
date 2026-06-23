# ============================================================
# 파일 위치: board_api/app/models/post.py
# 역할: DB 테이블 구조만 정의합니다. 쿼리 로직은 여기 없습니다.
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
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

    stat = relationship(
        "PostStat",
        back_populates="post",
        uselist=False,  # 1대 1
        cascade="all, delete-orphan"
    ) # 이 객체가 PostStat 객체를 속성으로 가지고 있지 않으면 가지고 있지 못한다. 그러니 속성값을 가지고 있어야 한다.

    Attachment = relationship(
        "Attachment",
        back_populates="post",
        uselist=True,   # 1대 다
        cascade="all, delete-orphan"    # 부모 삭제시 첨부파일도 자동 삭제
    )

class PostStat(Base) :
    __tablename__ = "post_stat"
    
    # unique=True → 1대1 보장 (post - PostStat의 관계가 1:1)
    id         = Column(Integer, primary_key=True, autoincrement=True)
    post_id    = Column(Integer, ForeignKey("post.id"),
                        unique=True, nullable=False)
    like_count = Column(Integer, default=0, comment="좋아요 수")
    created_at = Column(DateTime, default=datetime.now)

    post = relationship("Post", back_populates="stat")  # 이 객체를 가지고 있는 값 : Post

class Attachment(Base):
    __tablename__ = "attachment"

    # unique=True → 1대N (post - Attachment의 관계가 1:N)
    id         = Column(Integer, primary_key=True, autoincrement=True)
    post_id    = Column(Integer, ForeignKey("post.id"), nullable=False, unique=True)
    filename   = Column(String(255), nullable=False, comment="파일명")
    created_at = Column(DateTime, default=datetime.now)

    post = relationship("Post", back_populates="attachments")