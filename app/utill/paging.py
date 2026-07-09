# ============================================================
# 파일 위치: board_api/app/utils/paging.py
# ============================================================

import math

def calc_paging_block(
        page_no: int,
        page_size: int,
        total_post_cnt,
        page_cnt_per_block = 10,
) -> dict :
    """
    페이징 블럭 계산 함수.

    Args:
        page_no:            현재 페이지 번호 (1부터 시작)
        page_size:          페이지당 글 수
        total_post_cnt:     전체 글 수 (DB count 결과)
        page_cnt_per_block: 블럭당 페이지 수 (기본 10)

    Returns:
        페이징 및 블럭 정보 딕셔너리
    """
    # ---------------- 기본 페이징 -------------------------
    total_page_cnt = max(1, math.ceil(total_post_cnt / page_size))  # max : 글이 0개여도 페이지는 최소 1
    start_row_index = (page_no - 1) * page_size
    # DB 쿼리문에 들어갈 offset 값


    # ---------------- 페이징 블럭 계산 -------------------------
    total_paging_block_cnt = max(1, math.ceil(total_page_cnt / page_cnt_per_block)) # 전체 블럭 수
    page_block_of_current_page = math.ceil(page_no / page_cnt_per_block)  # 현재 페이지가 속한 블록 번호
    start_num = (page_block_of_current_page - 1) * page_cnt_per_block + 1  # 현재 블럭의 첫번째 페이지 번호
    end_num = min(page_block_of_current_page * page_cnt_per_block, total_page_cnt)  # 현재 블럭의 마지막 페이지 번호

    return {
        # 기본 페이징
        "page_no":           page_no,
        "page_size":         page_size,
        "total_post_cnt":    total_post_cnt,
        "total_page_cnt":    total_page_cnt,
        "start_row_index":   start_row_index,

        # 블럭 정보
        "page_cnt_per_block":               page_cnt_per_block,
        "total_paging_block_cnt":           total_paging_block_cnt,
        "page_block_of_current_page":       page_block_of_current_page,
        "start_num_of_current_paging_block": start_num,
        "end_num_of_current_paging_block":   end_num,

        # 이전/다음 블럭 존재 여부 (React 버튼 표시용)
        "has_prev_block": page_block_of_current_page > 1,
        "has_next_block": page_block_of_current_page < total_paging_block_cnt,
    }