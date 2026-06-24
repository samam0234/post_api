# ============================================================
# 파일 위치: board_api/app/schemas/post.py
# 역할: API의 입출력 데이터 구조를 정의합니다.
#       DB 모델과 분리함으로써 API 응답 형태를 독립적으로 관리합니다.
# ============================================================

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PostCreate(BaseModel) :
    """
    게시글 글 작성 요청 스키마 (body)
    """
    title:str = Field(..., min_length=1, max_length=200, description="글 제목")
    content:str = Field(..., min_length=1, description="본문")
    author:str = Field(..., min_length=1, max_length=12, description="작성자")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "FastAPI MVC 게시판",
                "content": "Repository, Service, Router로 분리해 작성합니다.",
                "author": "홍길동"
            }
        }
    }

# 게시글 수정용 request 스키마
class PostUpdate(BaseModel) :
    """
    PUT /post/{id} 요청 body(json data) - 수정될 필드만 전송
    """
    title:Optional[str] = Field(None, min_length=1, max_length=200, description="글 제목")
    content:Optional[str] = Field(None, min_length=1, description="글 본문")

class PostItem(BaseModel) :
    """목록 조회 응답 - 게시글 전체 조회용"""
    id:         int
    title:      str
    author:     str
    view_count: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}    # 위 속성(attributes)들을 json구조로 출력함

class PostDetail(BaseModel):
    """상세 조회 응답 (본문 포함) - 게시글 한건에 의한 응답"""
    id:         int
    title:      str
    content:    str
    author:     str
    view_count: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}    # 위 속성(attributes)들을 json구조로 출력함



# 페이징 처리에 필요한 스키마
class PagingInfo(BaseModel) :
    """
        프론트 단에서 페이징 처리를 할 때 필요한 모든 정보
        React에서 이 정보로 페이지 버튼을 렌더링합니다:
        {has_prev && <button>이전</button>}
        <span>{page} / {total_pages}</span>
        {has_next && <button>다음</button>}
    """
    total : int         # 전체 게시글 수
    total_pages : int   # 전체 페이지 수
    page:int            # 현재 페이지
    per_page:int        # 페이지당 항목 수
    has_prev:bool       # 이전 페이지 존재 여부
    has_next:bool       # 다음 페이지 존재 여부

class PostListResponse(BaseModel) :
    """
        PostItem의 리스트 형태 (게시글 전체 조회시 실제 반환되는 json)
        게시글 목록 + 페이징 정보
    """
    posts : List[PostItem]
    page_info:PagingInfo


# 첨부 파일 구간
class AttachmentIn(BaseModel) : 
    """
    첨부파일 등록 요청
    """
    filename:str = Field(..., min_length=1, description="파일명") 

class AttachmentOut(BaseModel):
    """첨부파일 응답"""
    id: int     # 첨부파일의 PK(Primary key)
    filename: str
    model_config = {"from_attributes": True}

class PostStatOut(BaseModel):
    """게시글 통계 응답"""
    like_count: int
    model_config = {"from_attributes": True}

class PostCreateWithAttachment(BaseModel):
    """게시글 + 첨부파일 동시 등록 요청"""
    title:       str = Field(..., min_length=1, max_length=200)
    content:     str = Field(..., min_length=1)
    author:      str = Field(..., min_length=1, max_length=50)
    attachments: List[AttachmentIn] = Field(
        default=[], description="첨부파일 목록 (없으면 빈 리스트)"
    )
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "트랜잭션 테스트 게시글",
                "content": "Post + Stat + Attachment 동시 저장합니다.",
                "author": "홍길동",
                "attachments": [
                    {"filename": "보고서.pdf"},
                    {"filename": "이미지.jpg"},
                ]
            }
        }
    }

class PostDetailWithStat(BaseModel):
    """게시글 상세 응답 (통계 + 첨부파일 포함)"""
    id: int; title: str; content: str; author: str
    view_count: int; created_at: datetime
    stat:        Optional[PostStatOut]  = None
    attachments: List[AttachmentOut]    = []
    model_config = {"from_attributes": True}