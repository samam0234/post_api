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
    
    def get_by_id(self, id:int) -> Optional[Post] :
        """
            id로 게시글 단건 조회, 없으면 None 반환
        """
        return self.db.get(Post, id)
    
    def increament_view_count(self, post:Post) -> Post :
        """
            id번 게시글의 조회수를 1증가시킨다.
        """
        post.view_count = post.view_count + 1
        self.db.commit()    # update 실행, db에 반영
        self.db.refresh(post)
        return post
    
    def get_post_list(self, offset:int = 0, limit:int = 10,
                      search:Optional[str] = None, author:Optional[str] = None, order_by:str = "latest"
                      ) -> List[Post] :
        """
            게시글 전체 목록을 반환
            페이징(offset, limit는 service단에서 계산된 값을 받아서) 처리
        """
        query = self.db.query(Post)     # "select * from post;" 쿼리문 자체
        
        # 검색어 조건문

        if search : # 제목 검색어가 있다면
            # LIKE '%검색어%'
            query.filter(Post.title.like(f"%{search}%"))

        if author : # 작성자 검색어가 있다면
            query.filter(Post.author == author)
        
        if order_by == "views" : # 정렬 조건이 조회수 순일때
            query = query.order_by(Post.view_count.desc())
        else :
            query = query.order_by(Post.created_at.desc())      # 작성일 최신순(default)

        # "limit 옵셋, 페이지당 출력될 행의 수"를 붙여 실행하여 반환
        return query.offset(offset=offset).limit(limit=limit).all() 

    def get_posts_count(self, search:Optional[str]=None, author:Optional[str]=None) -> int :
        """
            게시글의 전페 row수를 반환
            search, author 가 있으면 그 값에 따라 조회된 row수 반환
        """
        query = self.db.query(func.count(Post.id))  # 전체 글 수

        if search : # 제목 검색어가 있다면
            # LIKE '%검색어%'
            query = query.filter(Post.title.like(f"%{search}%"))

        if author : # 작성자 검색어가 있다면
            query = query.filter(Post.author == author)

        return query.scalar()
    
    def delete(self, post: Post) -> None:
        """게시글을 삭제합니다."""
        self.db.delete(post)
        self.db.commit()