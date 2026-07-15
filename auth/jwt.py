# ============================================================
# 파일 위치: board_api/app/auth/jwt.py
# 역할: JWT/비밀번호 관련 순수 함수만 둡니다. DB 접근 없음.
# ============================================================

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import os, secrets

SECRET_KEY = os.getenv("SECRET_KEY", "개발용-시크릿-키-반드시-변경할-것")
ALGORITHM = "HS256"     # HAMAC + SHA256 암호화 알고리즘

ACCESS_TOKEN_EXPIRE_MINUTES = 30      # Access Token: 30분 (짧게)
REFRESH_TOKEN_EXPIRE_DAYS   = 7       # Refresh Token: 7일 (길게)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2 진행시에도 같은 로직을 통해 jwt 인증이 수행되도록
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password:str) -> str :
    """
    평문 비밀번호 -> bcrypt 해시값으로 변환
    """
    return pwd_context.hash(password)

def verify_password(plain_password:str, hashed_password:str) -> bool :
    """
    입력된 비밀번호가 저장된 해시와 일치하는지 확인
    """
    return pwd_context.verify(plain_password, hashed_password)

# select * from users where username = 'admin' and password = md5('1234');
def create_access_token(data:dict) -> str :
    """
    Access Token 생성 — JWT, 서명 기반, 짧은 수명.

    jti(JWT ID)를 매번 랜덤하게 추가합니다.
    같은 사용자가 같은 순간 두 번 발급받아도 토큰이
    완전히 동일해지지 않도록 하기 위함입니다.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    to_encode["jti"] = secrets.token_hex(8)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_refresh_token() -> str :
    """
    Refresh Token 생성 — JWT가 아닌 랜덤 문자열입니다.
    DB에 저장해서 대조하는 방식이라 굳이 JWT일 필요가 없습니다.
    secrets.token_urlsafe: 암호학적으로 안전한 랜덤 문자열 생성기
    """
    return secrets.token_urlsafe(32)

def generate_refresh_token_expire() -> datetime :
    """
    리피레시 토큰의 만료일 생성
    """
    return datetime.now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

def get_current_username(token:str = Depends(oauth2_scheme)) -> str :
    """
    Access Token을 검증하고 username(sub)만 추출합니다.
    ⚠️ 여기서 DB 조회를 하지 않습니다. "누구인지"만 답합니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않거나 만료된 토큰입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None :
            raise credentials_exception
    except JWTError as e:
        # 서명이 틀리거나 만료된 경우
        raise credentials_exception
    
    return username