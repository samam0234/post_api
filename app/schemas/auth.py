# ============================================================
# 파일 위치: board_api/app/schemas/auth.py
# ============================================================

from pydantic import BaseModel, Field

# 회원가입 request용 스키마
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)
    name:     str = Field(..., min_length=1, max_length=50)

# 회원가입 response용 스키마
class UserInfo(BaseModel):
    username: str
    name:     str
    model_config = {"from_attributes": True}