# ============================================================
# 파일 위치: board_api/app/database.py
# ============================================================

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from dotenv import load_dotenv
from typing import Generator
import os

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "3308")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_NAME     = os.getenv("DB_NAME", "board_db")

DATABASE_URL = (                    # connection string(응용프로그램이 데이터베이스에 접속하기위한 정보의 문자열)
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,        # 미리 만들어 놓은 연결 객체. (필요하면 가져다 쓰고, 다 쓴 후에 반환한다.)
    pool_pre_ping=True  # idle모드 연결 자동 복구(mariadb, mysqsl db 필수)
)

sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)    # 데이터베이스에 연결하는 객체

class Base(DeclarativeBase) :   # SQLAlchemy ORM 모델들이 상속받는 기본 부모 클래스
    pass

def get_db() -> Generator[Session, None, None] :
    """
        FAST API에서 db세션을 요청마다 생성하고, 사용이 끝나면 자동으로 닫아주는 역할
    """
    
    db = sessionLocal()
    try :
        yield db    # 여기에서 db 연결 객체를 라우터 함수에 전달(양보)
    finally :
        # 라우터 함수에서 요청 처리가 끝나면 무조건 세션 종료
        db.close()

def check_db_connection() :
    """
        DB 연결이 정상 / 비정상 인지 테스트 하는 함수
    """
    try :
        with engine.connect() as conn :
            conn.execute(text("select 1"))
        print("MariaDB 연결 성공")
    except Exception as e:
        print(f"MariaDB 연결 실패 : {e}")
        raise       # Exception 예외 발생

if __name__=="__main__" :
    check_db_connection()