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

class PostListResponse(BaseModel) :
    """
        PostItem의 리스트 형태 (게시글 전체 조회시 실제 반환되는 json)
    """
    posts : List[PostItem]