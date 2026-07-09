# ============================================================
# 파일 위치: board_api/app/schemas/paging_schema.py
# ============================================================

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PagingSchema(BaseModel):
    """
    페이징 + 페이징 블럭 처리에 필요한 필드(속성)들
    """
    # 기본 페이징
    page_no: int
    page_size: int
    total_post_cnt: int
    total_page_cnt: int
    start_row_index: int
    
    # 블럭 정보
    page_cnt_per_block: int
    total_paging_block_cnt: int
    page_block_of_current_page: int
    start_num_of_current_paging_block: int
    end_num_of_current_paging_block: int
    
    # 이전/다음 블럭 존재 여부 (React 버튼 표시용)
    has_prev_block: bool
    has_next_block: bool

class PostItem(BaseModel):
    id: int; title: str; author: str
    view_count: int; created_at: datetime
    model_config = {"from_attributes": True}


class PageResponseDTO(BaseModel):
    """
    게시글 목록 + 페이징처리 정보
    """
    page_info:     PagingBlock
    board_list: List[PostItem]