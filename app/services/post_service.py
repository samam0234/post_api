# ============================================================
# 파일 위치: board_api/app/services/post_service.py
# 역할: 비즈니스 로직을 처리합니다.
#       페이징 계산, 조회수 증가, 404 검증 등이 여기 있습니다.
#       DB 접근은 Repository에 위임합니다.
# ============================================================

import math
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.schemas.post_schema import PostCreate, PostDetail
from app.repositories.post_repository import PostRepository

class PostService :
    def __init__(self, db:Session):
        self.db = db
        self.repo = PostRepository(db)  # repo 멤버변에 PostRepository객체 주입
    
    def create_post(self, data:PostCreate) -> PostDetail :
        """
            게시글 등록을 처리하는 서비스 함수
        """
        post = self.repo.insert(title=data.title, content=data.content, author=data.author)
        print(f"저장된 데이터 : {post.id}")

        # post객체가 PostDetail(Pydantic 객체)에 유효하지 검증한뒤 통과한뒤 PostDetail 객체 반환
        return PostDetail.model_validate(post)

    def read_post() :
        """
            게시글을 조회하는 서비스 함수
        """