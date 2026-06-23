# ============================================================
# 파일 위치: board_api/app/routers/post_router.py
# 역할: HTTP 요청 파라미터를 수신하고, Service를 호출하고, 응답을 반환합니다.
#       비즈니스 로직, DB 쿼리는 일절 없습니다.
#       "어떤 요청이 들어왔는가?", "어떤 서비스를 호출할 것이냐?", "어떻게 응답하냐?" 만 처리합니다.
# ============================================================

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.post_schema import PostCreate, PostDetail, PostListResponse, PostUpdate
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["게시판"])

# Service 객체를 Depends로 주입하기 위해 생성한 함수
def get_post_service(db:Session = Depends(get_db)) -> PostService:
  """
  DB 세션을 받아 PostService 인스턴스(객체)를 생성합니다.
  (서비스단에 DB세션을 넘겨주는 이유: 서비스 객체가 트랜잭션 처리의 주체이기 때문이다.)
  
  Router 함수에서 Depends(get_post_service)로 주입받습니다.

  장점: 테스트 시 이 함수만 교체하면 Mock Service를 주입할 수 있습니다.
  """
  
  return PostService(db) # PostService(서비스 단의 생성자 함수 호출)
  

@router.post("", response_model=PostDetail, status_code=201, summary = "게시글 등록")
def create_post(
  data: PostCreate,
  service: PostService = Depends(get_post_service)
):
  postDetail =service.create_post(data)  # 서비스단의 create_post() 호출
  return postDetail
  # PostService().create_post()
  
  
@router.get("/{id}", status_code=201, summary = "게시글 상세 조회")
def get_post(
  id: int = Path(..., ge=1),
  service:PostService=Depends(get_post_service)
): 
  return service.get_post_detail(id)

@router.get("", response_model=PostListResponse, summary="게시글 전체 조회")
def get_list(
  page:int = Query(1, ge=1, description="페이지번호"),
  per_page:int = Query(10, ge=10, le=100, description="페이지당 항목 수"),
  search:Optional[str] = Query(None, description="제목 검색어"),
  author:Optional[str] = Query(None, description="작성자 필터"),
  order_by:str=Query("latest", description="latest | views"),
  service:PostService=Depends(get_post_service)
) :
  return service.get_list(page, per_page, search, author, order_by)

@router.put("/{id}", response_model=PostDetail, summary="게시글 수정")
def update_post(
  id:int = Path(..., ge=1),
  data:PostUpdate = ...,
  service:PostService = Depends(get_post_service)
) :
    return service.Update_post(id, data=data)

@router.delete("/{id}", status_code=204, summary="게시글 삭제")
def delete_post(
    id: int = Path(..., ge=1), # 삭제할 게시글 번호
    service: PostService = Depends(get_post_service),
):
    service.delete_post(id)

