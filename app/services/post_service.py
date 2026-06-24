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

from app.schemas.post_schema import PostCreate, PostDetail, PostListResponse, PostItem, PagingInfo, PostUpdate, PostCreateWithAttachment, PostDetailWithStat
from app.repositories.post_repository import PostRepository

class PostService :
  
  def __init__(self, db:Session):
    self.db = db
    self.repo = PostRepository(db)  # repo 멤버변수에 PostRepository 객체 주입

  def _make_page_info(self, count:int, page:int, per_page:int) -> PagingInfo :
    """
        페이징 정보를 계산합니다.
        이 계산 로직은 비즈니스 로직이므로 Service에 위치합니다.
        (Repository는 offset/limit만 받아서 실행하고 계산하지 않습니다)
    """
    total_pages = max(1, math.ceil(count / per_page))
    
    return PagingInfo(
      total=count,
      total_pages=total_pages,
      page=page,
      per_page=per_page,
      has_prev=page > 1,
      has_next=page < total_pages
    )
  
  def _get_or_404(self, id:int) :
    """
        게시글을 조회하고 없으면 404 예외를 발생시킵니다.
        여러 메서드(조회, 수정, 삭제, 댓글 등)에서 공통으로 사용하는 검증 로직입니다.
    """
    post = self.repo.get_by_id(id)
    if not post :
      raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    return post
  
  def create_post(self, data:PostCreate) -> PostDetail :
    """
      게시글 등록을 처리하는 서비스 함수
    """
    post = self.repo.insert(title=data.title, content=data.content, author=data.author)
    print(f"저장된 게시글 : {post.id}")
    # post 객체가 PostDetail(Pydantic 객체)에 유효한지 검증한 뒤 통과되면 PostDetail 객체 반환.(검증 안되면 예외)
    return PostDetail.model_validate(post)
    
    
  def get_post_detail(self, id) -> PostDetail :
    """
      게시글을 조회하는 서비스 함수,
      해당 게시글의 조회수를 1 증가 하자.
      select + update 문이 하나의 db 세션에 의해 처리되었다. => 트랜잭션 처리
    """
    print(f"{id}번 글을 조회하자!!!!!!!!")
    
    post = self._get_or_404(id) # id번 글 조회
    post = self.repo.increament_view_count(post)  # 조회수 증가
    
    return PostDetail.model_validate(post)
  
  def get_list(self, page:int, per_page:int,
               search:Optional[str], author:Optional[str], order_by:str
               ) -> PostListResponse :
    """
        게시글 전체 조회
        - 페이징 처리를 위해 router단에서 page(현재 페이지 번호), per_page(페이지당 보여줄 글의 갯수)를 넘겨받음.
        - 검색어와 정렬 처리
    """
    # 1. 전체 데이터 수 조회(페이징 계산용)
    count = self.repo.get_posts_count(search, author)

    # 2. offset 계산
    # (현재페이지번호 - 1) * 페이지당 보여줄 글의 갯수
    offset = (page - 1) * per_page

    # 3. 페이징 된 게시글 목록 조회 - repository단 호출
    posts = self.repo.get_post_list(
      offset=offset, limit=per_page,
      search=search, author=author,
      order_by=order_by
    ) # List[Post] 타입 반환
    
    # Repository단에서 반환되는 List[Post]는 Post객체를 List[]에 감싼 타입이다. (json이 아님) => ORM에서 반환되는 기본값
    # 그래서 우리는 PostItem(한건의 게시글json) schema를 감싼 PostListResponse 스키마를 만들어 반환하는 구조를 선택한 것이다.
    return PostListResponse(
      posts = [PostItem.model_validate(p) for p in posts],
      page_info=self._make_page_info(count, page, per_page)
      )
  
  def Update_post(self, id:int, data:PostUpdate) -> PostDetail :
    post = self._get_or_404(id)
    changes = data.model_dump(exclude_none=True) # None필드 제외
    post = self.repo.Update(post, changes=changes)
    return PostDetail.model_validate(post)

  # ── 게시글 삭제 ───────────────────────────────────────────
  def delete_post(self, id: int) -> None:
      post = self._get_or_404(id)
      self.repo.delete(post)


  def create_post_with_Attachments(
      self, data:PostCreateWithAttachment
  ) -> PostDetailWithStat : 
    """
    Post + PostStat + Attachment 를 하나의 트랜잭션으로 저장합니다.

    ── 트랜잭션 책임 분담 ──────────────────────────────────
    Repository: db.add(), db.flush()  → "저장 준비"만
    Service:    db.commit()           → "확정 결정"
                db.rollback()         → "취소 결정"
    Router:     없음                  → DB 코드 전혀 없음
    ──────────────────────────────────────────────────────

    흐름:
        1. create_post_tx()  → Post flush (post.id 확보)
        2. create_stat()     → PostStat add (같은 트랜잭션)
        3. create_attachments() → Attachment add (같은 트랜잭션)
        4. commit()          → 모두 성공 → 한 번에 저장
       또는
        5. rollback()        → 하나라도 실패 → 전부 취소
    """
    try :
      post = self.repo.create_post_tx(data.title, data.content, data.author)  # post.id
      stat = self.repo.create_stat(post.id)
      filenames = [att.filename for att in data.attachments]
      self.repo.create_attachments(post.id, filenames)
      
      self.db.commit()
      self.db.refresh(post)

      return PostDetailWithStat.model_validate(post)
    except HTTPException as e:
      self.db.rollback()  #  지금까지의 모든 작업 rollback
      raise HTTPException(
        status_code=500,
        detail=f"게시글 등록 중 오류가 발생했습니다 {str(e)}"
      )
  def get_post_with_stat(self, id:int) -> PostDetailWithStat :
    """Post + PostStat + Attachment 조회"""
    post = self.repo.get_with_relations(id)
    if not post :
      raise HTTPException(
        status_code=500,
        detail=f"게시글을 가져오는 중 오류가 발생 했습니다."
      )
    return PostDetailWithStat.model_validate(post)