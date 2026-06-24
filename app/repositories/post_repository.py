# ============================================================
# 파일 위치: board_api/app/repositories/post_repository.py
# 역할: DB 쿼리만 작성합니다.
#       비즈니스 로직(페이징 계산, 조회수 증가 등)은 Service에 있습니다.
#       Service에서만 호출합니다. Router는 Repository를 직접 쓰지 않습니다.

#       여러개의 관계 테이블이 있을때 트랜잭션 처리가 필요하다 하더라도,
#       repository단에서 commit과 rollback을 절대 하지 않는다!!!!
#       commit과 rollback을 트랜잭션의 컨트롤 타워인 [service단]에서 담당한다.
#       Service단에서 트랜잭션을 컨트롤 하기 위해서, flush()는 해야 한다!!!!

# ============================================================

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
# 관계있는 테이블을 미리 json으로 함께 가져올때 사용한다.
# 예 : Post 조회시, PostStat, Attachment를 같이 가져올 수 있다.
# => N + 1 문제를 줄일 수 있다.
from sqlalchemy.orm import joinedload

from app.models.post_model import Post, PostStat, Attachment

class PostRepository :
    def __init__(self, db:Session):
        self.db = db

    def create_post_tx(self, title:str, content:str, author:str) -> Post :
        """
        게시글을 생성하고 flush로 id를 확보합니다.
        commit은 하지 않습니다.
        commit은 Service의 책임입니다.
        """
        post = Post(
            title=title, 
            content=content, 
            author=author,
            view_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.db.add(post)   # sqlAlchemy세션에 post 객체 등록
        # insert sql이 db에 전달 되어 실행되어 id가 생성된다.
        self.db.flush() # post.id를 사용할 수 있게 됨.

        # self.db.commit()    여기에서는 금지(트랜잭션 처리)

        return post
    
    def create_stat(self, post_id: int) -> PostStat:
        """
        PostStat을 생성합니다.
        commit은 하지 않습니다 — 같은 트랜잭션에 add만 합니다.
        """
        stat = PostStat(post_id=post_id, like_count=0, created_at=datetime.now())
        self.db.add(stat)
        self.db.flush() # stat.id 사용 가능(굳이 사용할 필요가 없다.)
        return stat
    
    def create_attachments(
        self, post_id: int, filenames: list[str]
        ) -> list[Attachment]:
        """
        첨부파일 목록을 생성합니다.
        commit은 하지 않습니다 — 같은 트랜잭션에 add만 합니다.
        """
        attachments = []
        for filename in filenames:
            att = Attachment(
                post_id=post_id, filename=filename, created_at=datetime.now()
            )
            self.db.add(att)
            attachments.append(att)
        return attachments

    def get_with_relations(self, post_id:int) -> Optional[Post] :
        """
        Post + PostStat + Attachment 를 한 번의 JOIN 쿼리로 조회합니다.
        joinedload → N+1 문제 방지
        """
        return (
            self.db.query(Post)             # Post 객체에 대한 기본 seclect 쿼리문
            .options(
                joinedload(Post.stat),      # post_stat 테이블과의 join (조건)
                joinedload(Post.attachments) # attachment 테이블과의 join (조건)
            )
            .filter(Post.id == post_id) # where절 (넘겨져온 게시글의 번호)
            .first()
        )

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
    
    def Update(self, post:Post, changes:dict) -> Post :
        """
        변경할 필드 딕셔너리를 받아 게시글을 수정합니다.
        post : 원래 글
        changes : 변경할 내용 들
        """
        for field, value in changes.items() :
            setattr(post, field, value)     # post객체의 속성을 field(key), value(value)로 세팅

        post.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(post)
        return post
    
    def delete(self, post: Post) -> None:
        """게시글을 삭제합니다."""
        self.db.delete(post)
        self.db.commit()