# ============================================================
# 파일 위치: board_api/app/repositories/post_repository.py
# 역할: DB 쿼리만 작성합니다.
#       비즈니스 로직(페이징 계산, 조회수 증가 등)은 Service에 있습니다.
#       Service에서만 호출합니다. Router는 Repository를 직접 쓰지 않습니다.
# ============================================================

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
from app.models.post_model import Post

class PostRepository :
    def __init__(self, db:Session):
        self.db = db

    def insert(self, title:str, content:str, author:str) -> Post : 
        """
            게시글을 DB에 저장하고 Post객체(id, create_at, update_at 포함)를 반환합니다.
        """
        print("게시글을 실제 디비에 저장하자! 요기는 레포지토리 단!!!!")
        post = Post(
            title=title, 
            content=content, 
            author=author,
            view_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.db.add(post)       # 실제 insert 쿼리문 실행
        self.db.commit()        # 데이터베이스에 영구 반영
        self.db.refresh(post)   # id가 존재하는 post 객체
        return post