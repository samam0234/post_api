# post_api 프로젝트 구조 가이드

FastAPI + MariaDB + SQLAlchemy로 만든 **게시판 API**의 **모든 코드 파일**을 계층·흐름·**알고리즘** 중심으로 설명하는 문서입니다.  
이 문서만 읽어도 "어떤 파일이 무엇을 하고, 요청이 어떤 순서·공식으로 처리되는지" 전체 그림을 이해할 수 있도록 작성했습니다.  
**페이징 알고리즘**은 목록 API의 필수 기능이므로 [섹션 7.1](#71--페이징-알고리즘-offset--limit-방식)에서 가장 상세히 다룹니다.

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [전체 디렉터리 구조](#2-전체-디렉터리-구조)
3. [아키텍처 한눈에 보기](#3-아키텍처-한눈에-보기)
4. [데이터 타입이 변하는 과정](#4-데이터-타입이-변하는-과정)
5. [파일별 상세 설명](#5-파일별-상세-설명)
6. [API 엔드포인트 전체 맵](#6-api-엔드포인트-전체-맵)
7. [**핵심 알고리즘 상세**](#7-핵심-알고리즘-상세) ← **페이징 알고리즘 중심**
8. [요청 흐름 시나리오 (3가지)](#8-요청-흐름-시나리오-3가지)
9. [의존성 주입 체인](#9-의존성-주입-체인)
10. [Model ↔ Schema 대응표](#10-model--schema-대응표)
11. [실행 및 환경 설정](#11-실행-및-환경-설정)
12. [새 기능 추가 가이드](#12-새-기능-추가-가이드)
13. [현재 코드 상태 메모](#13-현재-코드-상태-메모)

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | post_api (게시판 API) |
| **프레임워크** | FastAPI |
| **DB** | MariaDB (PyMySQL 드라이버) |
| **ORM** | SQLAlchemy 2.x |
| **검증/직렬화** | Pydantic v2 |
| **패턴** | Router → Service → Repository (MVC 변형) |

### 이 프로젝트가 지키는 규칙

```
Router     : HTTP만 담당 (URL, 파라미터, 상태코드, 응답 형태)
Service    : 비즈니스 로직 (페이징 계산·PagingInfo 생성, 404, 조회수 증가)
Repository : DB 쿼리만 (INSERT, SELECT, UPDATE)
Model      : DB 테이블 구조 (SQLAlchemy)
Schema     : API JSON 구조 (Pydantic)
```

**금지 사항:** Router가 Repository를 직접 호출하지 않습니다.  
**이유:** 역할을 분리하면 테스트·유지보수·확장이 쉬워집니다.

---

## 2. 전체 디렉터리 구조

```
post_api/
│
├── .env                          # DB 접속 정보 (환경 변수, git 제외 권장)
├── requirements.txt              # Python 패키지 의존성
├── STRUCTURE_GUIDE.md            # 이 문서
│
└── app/                          # 애플리케이션 루트 패키지
    ├── __init__.py               # 패키지 선언 (현재 비어 있음)
    ├── main.py                   # ★ 앱 진입점 — FastAPI 객체 생성
    ├── database.py               # ★ DB 연결, 세션, Base 클래스
    │
    ├── models/                   # DB 테이블 정의 (SQLAlchemy ORM)
    │   ├── __init__.py
    │   └── post_model.py         # Post 테이블
    │
    ├── schemas/                  # API 입출력 정의 (Pydantic)
    │   ├── __init__.py
    │   └── post_schema.py        # PostCreate, PostItem, PostDetail, PagingInfo, PostListResponse
    │
    ├── repositories/             # DB 쿼리 계층
    │   ├── __init__.py
    │   └── post_repository.py    # INSERT, SELECT, UPDATE
    │
    ├── services/                 # 비즈니스 로직 계층
    │   ├── __init__.py
    │   └── post_service.py       # 페이징, 404, 조회수 처리
    │
    └── routers/                  # HTTP 엔드포인트 계층
        ├── __init__.py
        └── post_router.py        # /posts API 라우트
```

### `__init__.py` 파일들

`app/` 하위 모든 `__init__.py`는 현재 `# __init__.py` 주석만 있습니다.  
Python이 해당 폴더를 **패키지**로 인식하게 하는 역할만 하며, 별도 로직은 없습니다.

---

## 3. 아키텍처 한눈에 보기

### 3.1 계층 구조

```mermaid
flowchart TB
    subgraph 진입["진입 계층"]
        MAIN["main.py\nFastAPI 앱 생성"]
        DB_CFG["database.py\nDB 연결·세션"]
    end

    subgraph HTTP["HTTP 계층"]
        ROUTER["post_router.py\n/posts 엔드포인트"]
    end

    subgraph 비즈니스["비즈니스 계층"]
        SERVICE["post_service.py\n페이징·404·조회수"]
    end

    subgraph 데이터접근["데이터 접근 계층"]
        REPO["post_repository.py\nSQL 쿼리"]
    end

    subgraph 정의["데이터 정의"]
        MODEL["post_model.py\nPost 테이블"]
        SCHEMA["post_schema.py\nJSON 스키마"]
    end

    DB[("MariaDB\npost 테이블")]

    MAIN --> ROUTER
    ROUTER --> SERVICE
    SERVICE --> REPO
    REPO --> MODEL
    REPO --> DB

    ROUTER -.->|"요청 검증"| SCHEMA
    SERVICE -.->|"응답 변환"| SCHEMA
    MODEL -.->|"ORM 매핑"| DB
```

### 3.2 호출 방향 (단방향)

```
클라이언트
    ↓ HTTP
main.py (라우터 등록)
    ↓
post_router.py
    ↓ Depends(get_post_service)
post_service.py
    ↓ self.repo = PostRepository(db)
post_repository.py
    ↓ SQLAlchemy Session
post_model.py (Post) ↔ MariaDB
```

---

## 4. 데이터 타입이 변하는 과정

API 요청 하나가 처리될 때 데이터 형태가 어떻게 바뀌는지 이해하는 것이 핵심입니다.

```mermaid
flowchart LR
    A["① JSON\n(HTTP Body/Query)"]
    B["② Pydantic Schema\nPostCreate 등"]
    C["③ Python 값\nstr, int"]
    D["④ SQLAlchemy Model\nPost 객체"]
    E["⑤ DB Row\nMariaDB 테이블"]
    F["⑥ Pydantic Schema\nPostDetail 등"]
    G["⑦ JSON\n(HTTP Response)"]

    A -->|"FastAPI 자동 파싱"| B
    B -->|"data.title 등"| C
    C -->|"repo.insert()"| D
    D -->|"db.add/commit"| E
    E -->|"db.get/query"| D
    D -->|"model_validate()"| F
    F -->|"response_model"| G
```

| 단계 | 형태 | 담당 |
|------|------|------|
| ① → ② | JSON → Pydantic | FastAPI + `post_schema.py` |
| ② → ④ | Pydantic → ORM | `post_service.py` → `post_repository.py` |
| ④ ↔ ⑤ | ORM ↔ DB Row | SQLAlchemy Session |
| ④ → ⑥ | ORM → Pydantic | `PostDetail.model_validate(post)` / `PostItem.model_validate(post)` |
| (목록) | count → PagingInfo | `_make_page_info()` — DB가 아닌 Service에서 계산 |
| ⑥ → ⑦ | Pydantic → JSON | FastAPI `response_model` (`PostListResponse` 등) |

---

## 5. 파일별 상세 설명

---

### 5.1 `app/main.py` — 애플리케이션 진입점

**역할:** FastAPI 앱을 만들고, 시작 시 DB 테이블을 생성하며, 라우터와 CORS를 등록합니다.

| 구성 요소 | 설명 |
|-----------|------|
| `lifespan()` | 앱 시작 시 `check_db_connection()` + `create_all()`로 테이블 자동 생성 |
| `app = FastAPI(...)` | API 메타정보(title, version)와 lifespan 연결 |
| `CORSMiddleware` | 브라우저(React 등)에서 API 호출 허용 (`allow_origins=["*"]`) |
| `app.include_router(post_router)` | `/posts` 라우트를 앱에 연결 |
| `GET /health` | 서버 생존 확인용 (`{"status": "ok"}`) |

**실행 명령:**
```bash
uvicorn app.main:app --reload
```

**맥락:** `main.py`는 비즈니스 로직을 갖지 않습니다. "앱 뼈대"만 조립하는 파일입니다.  
`from app import models`와 `from app.models import post_model` import는 SQLAlchemy가 `Post` 테이블 메타데이터를 `Base`에 등록하도록 하는 **필수 패턴**입니다.

```python
# lifespan 흐름
앱 시작 → DB 연결 테스트 → 없는 테이블 생성 → "테이블 준비 OK" 출력
앱 종료 → (yield 이후 정리 작업, 현재는 없음)
```

---

### 5.2 `app/database.py` — DB 연결 및 세션 관리

**역할:** MariaDB 연결 문자열 생성, 엔진·세션 팩토리 정의, 요청마다 DB 세션을 열고 닫습니다.

| 구성 요소 | 설명 |
|-----------|------|
| `load_dotenv()` | `.env` 파일에서 DB 접속 정보 로드 |
| `DATABASE_URL` | `mysql+pymysql://user:pass@host:port/dbname` 형식 |
| `engine` | 커넥션 풀 (pool_size=5, pool_pre_ping=True) |
| `sessionLocal` | DB 세션 생성 팩토리 |
| `Base` | 모든 ORM 모델이 상속하는 부모 클래스 |
| `get_db()` | FastAPI Depends용 Generator — 요청 끝나면 `db.close()` |
| `check_db_connection()` | `SELECT 1`로 연결 테스트 |

**환경 변수 (`.env`):**

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DB_HOST` | localhost | DB 서버 주소 |
| `DB_PORT` | 3308 | 포트 |
| `DB_USER` | root | 사용자 |
| `DB_PASSWORD` | 1234 | 비밀번호 |
| `DB_NAME` | board_db | 데이터베이스명 |

**맥락:** 모든 DB 작업은 `get_db()`가 만든 **하나의 Session**을 공유합니다.  
Service와 Repository가 같은 `db` 객체를 받기 때문에, 상세 조회 시 SELECT + UPDATE가 **같은 트랜잭션** 안에서 처리됩니다.

```
요청 시작 → get_db()가 sessionLocal() 생성 → yield db
         → Router/Service/Repository가 db 사용
요청 종료 → finally: db.close() → 커넥션 풀 반환
```

---

### 5.3 `app/models/post_model.py` — DB 테이블 정의 (ORM)

**역할:** `post` 테이블의 컬럼 구조만 정의합니다. 쿼리 로직은 없습니다.

**테이블: `post`**

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `id` | Integer | PK, autoincrement | 게시글 번호 |
| `title` | String(200) | NOT NULL | 제목 |
| `content` | Text | NOT NULL | 본문 |
| `author` | String(50) | NOT NULL | 작성자 |
| `view_count` | Integer | default=0 | 조회수 |
| `created_at` | DateTime | default=now | 작성 시각 |
| `updated_at` | DateTime | default=now, onupdate=now | 수정 시각 |

```python
class Post(Base):
    __tablename__ = "post"
    # Column 정의...
```

**맥락:** Model은 **DB 관점**의 데이터입니다. API 응답에 본문을 빼고 싶다면 Model을 바꾸지 않고 **Schema(PostItem)** 에서 필드를 조절합니다. 이것이 Model/Schema 분리의 핵심 이유입니다.

---

### 5.4 `app/schemas/post_schema.py` — API 입출력 정의 (Pydantic)

**역할:** 클라이언트와 주고받는 JSON의 형태·검증 규칙을 정의합니다. DB와 독립적입니다.

#### 스키마 관계도

```mermaid
classDiagram
    class PostCreate {
        +str title
        +str content
        +str author
    }
    class PostItem {
        +int id
        +str title
        +str author
        +int view_count
        +datetime created_at
        +datetime updated_at
    }
    class PostDetail {
        +int id
        +str title
        +str content
        +str author
        +int view_count
        +datetime created_at
        +datetime updated_at
    }
    class PagingInfo {
        +int total
        +int total_pages
        +int page
        +int per_page
        +bool has_prev
        +bool has_next
    }
    class PostListResponse {
        +List~PostItem~ posts
        +PagingInfo page_info
    }

    PostListResponse --> PostItem : posts 배열
    PostListResponse --> PagingInfo : page_info
    PostDetail --|> PostItem : content 추가
```

#### `PostCreate` — 작성 요청 (Request Body)

| 필드 | 타입 | 검증 | 설명 |
|------|------|------|------|
| `title` | str | 1~200자 | 글 제목 |
| `content` | str | 1자 이상 | 본문 |
| `author` | str | 1~12자 | 작성자 |

- 사용처: `POST /posts`
- `json_schema_extra.example`: Swagger `/docs`에 표시되는 예시 JSON

#### `PostItem` — 목록 한 건 (응답)

- `content` **없음** — 목록 API는 가볍게 유지
- `from_attributes: True` — SQLAlchemy `Post` 객체 → JSON 변환 허용

#### `PostDetail` — 상세 한 건 (응답)

- `PostItem` + `content`
- 사용처: `POST /posts` (등록 후), `GET /posts/{id}` (상세)

#### `PagingInfo` — 페이징 메타 (응답)

| 필드 | 설명 |
|------|------|
| `total` | 전체 게시글 수 |
| `total_pages` | 전체 페이지 수 (최소 1) |
| `page` | 현재 페이지 |
| `per_page` | 페이지당 항목 수 |
| `has_prev` | 이전 페이지 존재 여부 (`page > 1`) |
| `has_next` | 다음 페이지 존재 여부 (`page < total_pages`) |

- **계산 위치:** `post_service.py`의 `_make_page_info()` (비즈니스 로직이므로 Service에 위치)
- React 프론트에서 `{has_prev && <button>이전</button>}` 형태로 페이지 버튼을 렌더링합니다.

#### `PostListResponse` — 목록 + 페이징 래퍼 (응답)

`PagingInfo`를 먼저 정의한 뒤, `PostListResponse`가 `posts`와 `page_info`를 함께 담습니다.

```json
{
  "posts": [
    { "id": 1, "title": "...", "author": "홍길동", "view_count": 0, "created_at": "...", "updated_at": "..." }
  ],
  "page_info": {
    "total": 45,
    "total_pages": 5,
    "page": 2,
    "per_page": 10,
    "has_prev": true,
    "has_next": true
  }
}
```

- 사용처: `GET /posts`
- `page_info`는 Service의 `_make_page_info()`가 생성합니다.

---

### 5.5 `app/repositories/post_repository.py` — DB 쿼리 계층

**역할:** SQLAlchemy Session으로 DB에 직접 접근합니다. 비즈니스 판단은 하지 않습니다.

| 메서드 | 하는 일 | 반환 |
|--------|---------|------|
| `__init__(db)` | Session을 멤버로 보관 | — |
| `insert(title, content, author)` | Post 생성 → add → commit → refresh | `Post` |
| `get_by_id(id)` | PK로 단건 조회 | `Post` 또는 `None` |
| `increament_view_count(post)` | view_count + 1 → commit → refresh | `Post` |
| `get_post_list(offset, limit)` | OFFSET/LIMIT 페이징 조회 | `List[Post]` |
| `get_posts_count()` | `COUNT(id)` 전체 건수 | `int` |

**맥락:**
- `offset`, `limit`는 Service에서 계산한 값을 **그대로 받아** 실행합니다. Repository는 "몇 페이지인지" 모릅니다.
- `get_by_id`가 `None`을 반환하면 404 처리는 **Service**의 `_get_or_404()`가 담당합니다.
- `insert` 안에서 `created_at`, `updated_at`을 `datetime.now()`로 직접 넣고 있습니다. (Model default와 중복이지만, 명시적 설정)

```sql
-- insert() 가 실행하는 것과 동일한 개념
INSERT INTO post (title, content, author, view_count, created_at, updated_at)
VALUES (?, ?, ?, 0, NOW(), NOW());

-- get_post_list(offset=10, limit=10)
SELECT * FROM post LIMIT 10 OFFSET 10;

-- get_posts_count()
SELECT COUNT(post.id) FROM post;
```

---

### 5.6 `app/services/post_service.py` — 비즈니스 로직 계층

**역할:** "무엇을 할지"를 결정합니다. DB 접근은 Repository에 위임합니다.

| 메서드 | 하는 일 | 입출력 |
|--------|---------|--------|
| `__init__(db)` | `PostRepository(db)` 생성 | — |
| `_make_page_info(count, page, per_page)` | 페이징 메타 계산 → `PagingInfo` 생성 | `int` × 3 → `PagingInfo` |
| `_get_or_404(id)` | 글 없으면 HTTP 404 발생 | `Post` |
| `create_post(data)` | repo.insert → PostDetail 변환 | `PostCreate` → `PostDetail` |
| `get_post_detail(id)` | 조회 + 조회수 +1 → PostDetail 변환 | `int` → `PostDetail` |
| `get_list(page, per_page)` | count·offset 계산 → 목록 조회 → `posts` + `page_info` 조립 | → `PostListResponse` |

#### `create_post` 흐름

```
PostCreate (Pydantic)
  → data.title, data.content, data.author 추출
  → repo.insert(...)
  → Post (ORM, id·날짜 포함)
  → PostDetail.model_validate(post)
  → PostDetail (Pydantic) 반환
```

#### `get_post_detail` 흐름

```
id
  → _get_or_404(id)        # 없으면 404
  → repo.increament_view_count(post)
  → PostDetail.model_validate(post)
```

#### `_make_page_info` — 페이징 메타 계산

```python
total_pages = max(1, math.ceil(count / per_page))

PagingInfo(
  total=count,
  total_pages=total_pages,
  page=page,
  per_page=per_page,
  has_prev=page > 1,
  has_next=page < total_pages,
)
```

- `total_pages`는 `max(1, ...)`로 **최소 1페이지**를 보장합니다. (게시글이 0건이어도 1페이지)
- 이 계산은 Repository가 아닌 **Service**에 있습니다. Repository는 `offset`/`limit`만 받아 실행합니다.

#### `get_list` 페이징 계산

```
count = repo.get_posts_count()                    # 전체 N건
offset = (page - 1) * per_page                    # 건너뛸 행 수
posts = repo.get_post_list(offset, per_page)      # List[Post]
page_info = self._make_page_info(count, page, per_page)

PostListResponse(
  posts = [PostItem.model_validate(p) for p in posts],
  page_info = page_info
)
```

**맥락:** Service가 ORM `List[Post]`와 페이징 메타를 API용 `PostListResponse`로 바꿉니다.  
Repository는 JSON·페이지 번호를 모르고, Router는 SQL을 모릅니다. **변환·계산 지점이 Service**입니다.  
→ 페이징 알고리즘 전체는 [섹션 7.1](#71--페이징-알고리즘-offset--limit-방식) 참고

---

### 5.7 `app/routers/post_router.py` — HTTP 엔드포인트

**역할:** URL·HTTP 메서드·파라미터·응답 코드만 처리합니다.

```python
router = APIRouter(prefix="/posts", tags=["게시판"])
```

| 엔드포인트 | 함수 | 요청 | 응답 | 상태코드 |
|------------|------|------|------|----------|
| `POST /posts` | `create_post` | Body: `PostCreate` | `PostDetail` | 201 |
| `GET /posts/{id}` | `get_post` | Path: `id` (≥1) | `PostDetail` | 201* |
| `GET /posts` | `get_list` | Query: `page`, `per_page`, `search`, `author`, `order_by` | `PostListResponse` | 200 |

\* `GET /posts/{id}`의 `status_code=201`은 일반적이지 않습니다. 조회는 보통 200입니다. (섹션 13)

#### `get_list` Query 파라미터 (Router 검증)

| 파라미터 | 기본값 | 제약 | 현재 동작 |
|----------|--------|------|-----------|
| `page` | 1 | ≥ 1 | Service에 전달됨 |
| `per_page` | 10 | 10 ~ 100 | Service에 전달됨 |
| `search` | None | — | Swagger에만 노출, **Service 미전달** |
| `author` | None | — | Swagger에만 노출, **Service 미전달** |
| `order_by` | `"latest"` | — | Swagger에만 노출, **Service 미전달** |

#### `get_post_service()` — 의존성 주입 헬퍼

```python
def get_post_service(db: Session = Depends(get_db)) -> PostService:
    return PostService(db)
```

모든 라우트 함수는 `service: PostService = Depends(get_post_service)`로 Service를 받습니다.  
페이징·검색·정렬 **알고리즘은 Router에 없고** Service/Repository에 있습니다. (섹션 7 참고)

---

### 5.8 `requirements.txt` — 패키지 의존성

| 패키지 | 역할 |
|--------|------|
| `fastapi` | 웹 API 프레임워크 |
| `uvicorn` | ASGI 서버 (실행) |
| `sqlalchemy` | ORM |
| `PyMySQL` | MariaDB/MySQL 드라이버 |
| `pydantic` | 데이터 검증·스키마 |
| `python-dotenv` | `.env` 환경 변수 로드 |
| `python-multipart` | 폼 데이터 처리 (FastAPI 의존) |
| `openai` | (현재 게시판 코드에서 직접 사용하지 않음) |

---

## 6. API 엔드포인트 전체 맵

| 메서드 | URL | Query/Body | 응답 Schema | 처리 Service 메서드 |
|--------|-----|------------|-------------|---------------------|
| `POST` | `/posts` | Body: `PostCreate` | `PostDetail` | `create_post()` |
| `GET` | `/posts/{id}` | Path: `id` | `PostDetail` | `get_post_detail()` |
| `GET` | `/posts` | `page`, `per_page`, `search`, `author`, `order_by` | `PostListResponse` (`posts` + `page_info`) | `get_list()` |
| `GET` | `/health` | — | `{"status":"ok"}` | (main.py 직접) |

### Swagger 문서

서버 실행 후: http://127.0.0.1:8000/docs

---

## 7. 핵심 알고리즘 상세

이 프로젝트의 각 기능이 **어떤 순서·공식·조건**으로 동작하는지 알고리즘 관점에서 정리합니다.  
그중 **페이징**은 목록 API의 필수 기능이므로 가장 상세히 설명합니다.

---

### 7.1 ★ 페이징 알고리즘 (Offset / Limit 방식)

#### 왜 페이징이 필요한가?

게시글이 1,000건이면 `SELECT * FROM post`로 전부 가져오면 응답이 느려지고 프론트 렌더링도 무거워집니다.  
**한 번에 `per_page`건만 잘라서** 보내고, 프론트는 `page_info`로 페이지 버튼을 그립니다.

이 프로젝트는 **Offset/Limit 페이징**을 사용합니다.

```
offset = (page - 1) × per_page   ← 앞에서 건너뛸 행 수
limit  = per_page                ← 이번에 가져올 행 수
```

#### 페이징 알고리즘 전체 흐름

```mermaid
flowchart TD
    A["① Router: page, per_page 검증\n(page≥1, 10≤per_page≤100)"]
    B["② Service: count = get_posts_count()\n전체 게시글 수 N"]
    C["③ Service: offset = (page-1) × per_page"]
    D["④ Repository: get_post_list(offset, limit)\nSELECT ... OFFSET ? LIMIT ?"]
    E["⑤ Service: _make_page_info(count, page, per_page)\nPagingInfo 생성"]
    F["⑥ Service: PostItem 변환 + PostListResponse 조립"]
    G["⑦ Router: JSON 응답\n{ posts, page_info }"]

    A --> B --> C --> D --> E --> F --> G
```

**핵심:** DB 쿼리는 **2번** 실행됩니다.

| 순서 | 쿼리 | 목적 |
|------|------|------|
| 1 | `COUNT(id)` | 전체 건수 → `total_pages`, `has_next` 계산 |
| 2 | `SELECT ... OFFSET ... LIMIT ...` | 현재 페이지 데이터만 조회 |

#### 시각적 이해 — 전체 45건, per_page=10, page=2

```
인덱스(0부터):  [0..9]  [10..19]  [20..29]  [30..39]  [40..44]
페이지 번호:      1페이지   2페이지   3페이지   4페이지   5페이지
                  ↑ 건너뜀   ↑ 이번에 반환 (10건)
offset = (2-1)×10 = 10
```

#### `get_list()` 알고리즘 (의사코드)

```
함수 get_list(page, per_page):

  // Step 1: 전체 건수 (페이징 메타 계산의 기준)
  count ← repo.get_posts_count()

  // Step 2: offset 계산 — "몇 번째 행부터 읽을지"
  offset ← (page - 1) × per_page

  // Step 3: 현재 페이지 데이터만 DB에서 조회
  posts ← repo.get_post_list(offset=offset, limit=per_page)

  // Step 4: 페이징 메타 생성
  page_info ← _make_page_info(count, page, per_page)

  // Step 5: ORM → Pydantic 변환 후 응답 조립
  RETURN PostListResponse(
    posts = [PostItem.model_validate(p) for p in posts],
    page_info = page_info
  )
```

**실제 코드 위치:** `app/services/post_service.py` → `get_list()`

#### `_make_page_info()` 알고리즘 (의사코드)

```
함수 _make_page_info(count, page, per_page):

  // 전체 페이지 수 — 올림(ceil)으로 마지막 불완전 페이지 포함
  // max(1, ...) — 게시글 0건이어도 최소 1페이지 보장
  total_pages ← max(1, ceil(count / per_page))

  RETURN PagingInfo(
    total       = count,
    total_pages = total_pages,
    page        = page,
    per_page    = per_page,
    has_prev    = (page > 1),
    has_next    = (page < total_pages)
  )
```

**실제 코드 위치:** `app/services/post_service.py` → `_make_page_info()`

#### 페이징 공식 정리

| 출력 필드 | 공식 | 의미 |
|-----------|------|------|
| `offset` | `(page - 1) × per_page` | DB에서 건너뛸 행 수 |
| `total` | `COUNT(id)` | 조건에 맞는 전체 게시글 수 |
| `total_pages` | `max(1, ⌈total / per_page⌉)` | 전체 페이지 수 |
| `has_prev` | `page > 1` | 1페이지보다 크면 이전 버튼 표시 |
| `has_next` | `page < total_pages` | 마지막 페이지가 아니면 다음 버튼 표시 |

`⌈ ⌉`는 올림(ceil)입니다. 예: total=45, per_page=10 → ⌈4.5⌉ = **5페이지**

#### 경계 케이스 (반드시 이해할 것)

| 상황 | count | page | per_page | 결과 |
|------|-------|------|----------|------|
| 게시글 없음 | 0 | 1 | 10 | `posts=[]`, `total_pages=1`, `has_prev=false`, `has_next=false` |
| 마지막 페이지 (불완전) | 45 | 5 | 10 | `posts` 5건, `total_pages=5`, `has_next=false` |
| 첫 페이지 | 45 | 1 | 10 | `has_prev=false`, `has_next=true` |
| 존재하지 않는 페이지 | 45 | 99 | 10 | `posts=[]` (빈 배열), `page_info.page=99`, `has_next=false` |

> **참고:** 현재 코드는 `page`가 `total_pages`를 초과해도 404를 내지 않고 **빈 목록**을 반환합니다.  
> 엄격하게 막으려면 Service에서 `page > total_pages`일 때 400/404를 추가하는 방식으로 확장할 수 있습니다.

#### 계층별 역할 — 왜 이렇게 나누나?

| 계층 | 페이징에서 하는 일 | 하지 않는 일 |
|------|-------------------|-------------|
| **Router** | `page`, `per_page` 범위 검증 (FastAPI Query) | offset 계산, COUNT 쿼리 |
| **Service** | offset·total_pages·has_prev/next **계산** | SQL 직접 작성 |
| **Repository** | `OFFSET`/`LIMIT`/`COUNT` **실행만** | page 번호 해석 |

페이지 번호(`page`)를 SQL이 이해하는 `offset`으로 바꾸는 것은 **비즈니스 로직**이므로 Service에 둡니다.

#### 프론트엔드(React) 연동 알고리즘

`PagingInfo`는 React가 **추가 계산 없이** 버튼을 그리도록 설계되었습니다.

```jsx
// page_info를 그대로 사용
{page_info.has_prev && <button onClick={() => setPage(page - 1)}>이전</button>}
<span>{page_info.page} / {page_info.total_pages}</span>
{page_info.has_next && <button onClick={() => setPage(page + 1)}>다음</button>}
```

API 호출 예:
```
GET /posts?page=2&per_page=10
```

---

### 7.2 게시글 등록 알고리즘

```
입력: PostCreate (title, content, author) — Pydantic이 1차 검증

1. Router: JSON body → PostCreate 변환 (실패 시 422)
2. Service.create_post(data):
     post ← repo.insert(title, content, author)
3. Repository.insert():
     Post 객체 생성 (view_count=0, created_at/updated_at=now)
     db.add → db.commit → db.refresh
4. Service: PostDetail.model_validate(post)
5. Router: 201 + PostDetail JSON 반환
```

**DB에 자동 생성되는 값:** `id`, `view_count`, `created_at`, `updated_at` — 클라이언트가 보내지 않습니다.

---

### 7.3 상세 조회 + 조회수 증가 알고리즘

```
입력: id (Path, ge=1)

1. Service.get_post_detail(id):
     post ← _get_or_404(id)           // 없으면 HTTP 404
     post ← repo.increament_view_count(post)
2. Repository:
     get_by_id(id)        → SELECT BY PK
     view_count += 1      → UPDATE + commit + refresh
3. Service: PostDetail.model_validate(post)
4. Router: PostDetail JSON 반환
```

**트랜잭션 맥락:** `get_db()`가 제공한 **동일 Session**으로 SELECT와 UPDATE가 처리됩니다.

---

### 7.4 404 검증 알고리즘 (`_get_or_404`)

```
함수 _get_or_404(id):
  post ← repo.get_by_id(id)
  IF post IS NULL:
    RAISE HTTPException(404, "게시글을 찾을 수 없습니다.")
  RETURN post
```

여러 기능(수정, 삭제, 댓글 등)에서 **공통으로 재사용**할 수 있도록 private 메서드로 분리했습니다.

---

### 7.5 DB 세션 생명주기 알고리즘 (`get_db`)

```
요청 도착:
  db ← sessionLocal()     // 커넥션 풀에서 세션 할당
  yield db                // Router → Service → Repository에 전달

요청 종료 (성공/실패 무관):
  db.close()              // 세션 종료, 커넥션 풀 반환
```

`try/finally` 구조이므로 예외가 나도 세션이 반드시 닫힙니다.

---

### 7.6 요청 데이터 검증 알고리즘 (Pydantic)

FastAPI는 Router 진입 **전에** Pydantic 검증을 수행합니다.

| 스키마 | 검증 규칙 | 실패 시 |
|--------|-----------|---------|
| `PostCreate.title` | 1~200자 | 422 Unprocessable Entity |
| `PostCreate.content` | 1자 이상 | 422 |
| `PostCreate.author` | 1~12자 | 422 |
| Query `page` | ≥ 1 | 422 |
| Query `per_page` | 10 ~ 100 | 422 |

검증 통과 후에만 Service가 호출됩니다.

---

## 8. 요청 흐름 시나리오 (3가지)

### 8.1 게시글 등록 `POST /posts`

```mermaid
sequenceDiagram
    participant C as 클라이언트
    participant M as main.py
    participant R as post_router
    participant S as post_service
    participant Rep as post_repository
    participant DB as MariaDB

    C->>M: POST /posts + JSON body
    M->>R: create_post 라우팅
    Note over R: JSON → PostCreate (Pydantic 검증)
    R->>S: create_post(data)
    S->>Rep: insert(title, content, author)
    Rep->>DB: INSERT
    DB-->>Rep: Post (id 포함)
    Rep-->>S: Post
    Note over S: PostDetail.model_validate(post)
    S-->>R: PostDetail
    R-->>C: 201 + JSON
```

### 8.2 게시글 상세 `GET /posts/3`

```mermaid
sequenceDiagram
    participant C as 클라이언트
    participant R as post_router
    participant S as post_service
    participant Rep as post_repository
    participant DB as MariaDB

    C->>R: GET /posts/3
    R->>S: get_post_detail(3)
    S->>Rep: get_by_id(3)
    Rep->>DB: SELECT BY PK
    DB-->>Rep: Post
    Rep-->>S: Post
    S->>Rep: increament_view_count(post)
    Rep->>DB: UPDATE view_count
    DB-->>Rep: Post (갱신)
    Rep-->>S: Post
    Note over S: PostDetail.model_validate(post)
    S-->>R: PostDetail
    R-->>C: JSON 응답
```

**트랜잭션 맥락:** `get_db()`가 만든 동일 Session으로 SELECT와 UPDATE가 이어지므로, 하나의 요청 안에서 조회와 조회수 증가가 같은 연결로 처리됩니다.

### 8.3 게시글 목록 `GET /posts?page=2&per_page=10`

```mermaid
sequenceDiagram
    participant C as 클라이언트
    participant R as post_router
    participant S as post_service
    participant Rep as post_repository
    participant DB as MariaDB

    C->>R: GET /posts?page=2&per_page=10
    R->>S: get_list(2, 10)
    S->>Rep: get_posts_count()
    Rep->>DB: SELECT COUNT(id)
    DB-->>Rep: 45
    Rep-->>S: count=45
    Note over S: offset = (2-1) × 10 = 10
    S->>Rep: get_post_list(offset=10, limit=10)
    Rep->>DB: SELECT ... OFFSET 10 LIMIT 10
    DB-->>Rep: List[Post]
    Rep-->>S: posts
    Note over S: _make_page_info(45, 2, 10)
    Note over S: PostListResponse(posts, page_info) 조립
    S-->>R: PostListResponse
    R-->>C: JSON (posts + page_info)
```

**처리 단계:**

```
1. Router   page=2, per_page=10 수신 (Query 검증: page≥1, 10≤per_page≤100)
2. Service  count = get_posts_count()              → 예: 45건
            offset = (2-1) * 10 = 10
3. Repository
            get_post_list(offset=10, limit=10)       → 11~20번째 글
4. Service  _make_page_info(45, 2, 10)             → PagingInfo 생성
            PostItem 변환 후 PostListResponse 조립
5. Router   { "posts": [...], "page_info": {...} } JSON 반환
```

> 페이징 공식·경계 케이스·프론트 연동 등 **알고리즘 상세**는 [섹션 7.1](#71--페이징-알고리즘-offset--limit-방식)을 참고하세요.

---

## 9. 의존성 주입 체인

FastAPI `Depends`가 요청마다 객체를 자동으로 만들어 연결합니다.

```
HTTP 요청 도착
│
├─ get_db()                         [database.py]
│    └─ sessionLocal() → Session 생성
│         │
│         └─ get_post_service(db)   [post_router.py]
│              └─ PostService(db)   [post_service.py]
│                   └─ PostRepository(db)  [post_repository.py]
│
요청 처리 완료
└─ get_db() finally → db.close()
```

**왜 이렇게 하나?**

| 장점 | 설명 |
|------|------|
| 세션 자동 관리 | 요청마다 열고, 끝나면 반드시 닫음 |
| 테스트 용이 | `get_post_service`를 Mock으로 교체 가능 |
| 결합도 감소 | Router는 Service 인터페이스만 알면 됨 |

---

## 10. Model ↔ Schema 대응표

| DB 컬럼 (`Post`) | `PostCreate` | `PostItem` | `PostDetail` | `PagingInfo` (`page_info`) |
|------------------|:------------:|:----------:|:------------:|:--------------------------:|
| `id` | — | O | O | — |
| `title` | O (입력) | O | O | — |
| `content` | O (입력) | — | O | — |
| `author` | O (입력) | O | O | — |
| `view_count` | — | O | O | — |
| `created_at` | — | O | O | — |
| `updated_at` | — | O | O | — |
| (페이징 메타) | — | — | — | O |

- **PostCreate**: 클라이언트가 보내는 값만 (id·조회수·날짜는 서버/DB가 생성)
- **PostItem / PostDetail**: DB에서 읽은 값을 JSON으로 반환
- **PagingInfo**: DB 컬럼이 아닌 Service `_make_page_info()`가 계산하는 값
- **PostListResponse**: `posts`(PostItem 배열) + `page_info`(PagingInfo)를 한 응답에 묶어 반환

---

## 11. 실행 및 환경 설정

### 11.1 사전 준비

1. MariaDB 실행 및 `board_db` 데이터베이스 생성
2. `.env` 파일에 접속 정보 설정
3. 가상환경 생성 및 패키지 설치

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 11.2 서버 실행

```bash
uvicorn app.main:app --reload
```

### 11.3 확인

| URL | 용도 |
|-----|------|
| http://127.0.0.1:8000/docs | Swagger API 문서 |
| http://127.0.0.1:8000/health | 서버 상태 |
| http://127.0.0.1:8000/posts | 게시글 목록 |

---

## 12. 새 기능 추가 가이드

예: "게시글 수정 API"를 추가한다면

| 순서 | 파일 | 작업 |
|------|------|------|
| 1 | `schemas/post_schema.py` | `PostUpdate` 스키마 추가 |
| 2 | `models/post_model.py` | (컬럼 변경 필요 시만) |
| 3 | `repositories/post_repository.py` | `update(id, ...)` 쿼리 추가 |
| 4 | `services/post_service.py` | 검증 + repo 호출 + 응답 변환 |
| 5 | `routers/post_router.py` | `PUT /posts/{id}` 엔드포인트 추가 |

**항상 지킬 순서:** Schema → Model → Repository → Service → Router

### 계층별 수정 범위 요약

| 추가하려는 것 | 수정 파일 |
|---------------|-----------|
| URL, HTTP 메서드 | `routers/post_router.py` |
| 페이징, 검증, 404 | `services/post_service.py` |
| SQL 쿼리 | `repositories/post_repository.py` |
| 테이블/컬럼 | `models/post_model.py` |
| 요청/응답 JSON | `schemas/post_schema.py` |
| DB 연결 설정 | `database.py` |
| 앱 전역 설정, CORS | `main.py` |

---

## 13. 현재 코드 상태 메모

문서와 실제 코드를 맞춰 이해할 때 참고할 사항입니다.

| 항목 | 현재 상태 |
|------|-----------|
| `PagingInfo` | `PostListResponse.page_info`로 연결 완료. `_make_page_info()`에서 생성 (섹션 7.1) |
| `GET /posts` 응답 | `posts` + `page_info` 두 필드를 함께 반환 |
| `search` / `author` / `order_by` | Router Query로 정의됨. **Service·Repository에 미연결** |
| `GET /posts/{id}` 상태코드 | `201`로 설정됨 (조회 API는 보통 `200`) |
| `author` 길이 | Schema 최대 12자, DB Model은 String(50) — 불일치 |
| `page > total_pages` | 404 없이 빈 `posts` 반환 (섹션 7.1 경계 케이스) |
| `post_schema.py` | `Optional` import 있으나 미사용 |
| `post_service.py` | `Optional` import 있으나 미사용 |
| `post_router.py` | `PostItem` import 있으나 미사용. `Optional`은 `search`/`author`에 사용 |

---

## 부록: 파일 → 역할 빠른 참조

| 파일 | 한 줄 요약 |
|------|-----------|
| `main.py` | 앱 생성, 테이블 자동 생성, 라우터·CORS 등록 |
| `database.py` | DB 연결, 세션 생성/종료, Base 클래스 |
| `post_model.py` | `post` 테이블 컬럼 정의 |
| `post_schema.py` | API JSON 요청/응답 구조·검증 |
| `post_repository.py` | INSERT, SELECT, UPDATE 쿼리 |
| `post_service.py` | 페이징 계산(`_make_page_info`)·404·조회수 등 비즈니스 로직 |
| `post_router.py` | `/posts` HTTP 엔드포인트 |
| `requirements.txt` | pip 패키지 목록 |
| `.env` | DB 접속 환경 변수 |
| `__init__.py` (6개) | Python 패키지 선언 (로직 없음) |