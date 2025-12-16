# 회원가입 (Sign Up) 개발 계획

## 1. 개요

### 1.1 목적
네이버 검색 순위 트래킹 서비스의 사용자 계정 생성 기능을 구현합니다.

### 1.2 범위
- 아이디와 비밀번호를 이용한 기본 회원가입
- 비밀번호 암호화 및 안전한 저장
- 중복 아이디 방지

---

## 2. 요구사항 정의

### 2.1 기능 요구사항

#### 2.1.1 회원가입 입력 정보
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| username | 문자열 | O | 로그인 아이디 |
| password | 문자열 | O | 비밀번호 |

#### 2.1.2 검증 규칙
- **username (아이디)**: 중복 불가
- **password (비밀번호)**: 제한 없음

> **v1.0 정책**: 최소한의 검증만 수행합니다. 글자 수 제한, 문자 조합 규칙, 형식 검증 등은 추후 버전에서 필요 시 추가합니다.

#### 2.1.3 회원가입 프로세스
1. 클라이언트가 아이디, 비밀번호 전송
2. 아이디 중복 확인
3. 비밀번호 해싱 (bcrypt)
4. 데이터베이스에 사용자 정보 저장
5. 생성된 사용자 정보 반환 (비밀번호 제외)

#### 2.1.4 응답 처리
- 성공 시: HTTP 201 Created + 생성된 사용자 정보
- 실패 시: 적절한 HTTP 상태 코드 + 에러 메시지

### 2.2 비기능 요구사항

#### 2.2.1 보안
- 비밀번호는 평문 저장 금지
- bcrypt 알고리즘 사용 (cost factor: 12)
- 민감 정보 로깅 금지
- 응답에 비밀번호 포함 금지

#### 2.2.2 성능
- 회원가입 응답 시간: 3초 이내
- bcrypt 해싱으로 인한 지연 고려

---

## 3. 데이터 모델 설계

### 3.1 User 테이블

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| id | Integer | PK, Auto Increment | 사용자 고유 ID |
| username | String | Unique, Not Null, Index | 로그인 아이디 |
| hashed_password | String(255) | Not Null | bcrypt 해싱된 비밀번호 |
| created_at | DateTime | Not Null, Default: now() | 가입 일시 |
| updated_at | DateTime | Not Null, Default: now() | 수정 일시 |

### 3.2 인덱스
- `username`: Unique Index (로그인, 중복 확인 최적화)

---

## 4. API 설계

### 4.1 엔드포인트

#### POST /api/v1/auth/signup

회원가입을 처리합니다.

**요청**
```json
{
  "username": "johndoe",
  "password": "mypassword"
}
```

**성공 응답 (201 Created)**
```json
{
  "id": 1,
  "username": "johndoe",
  "created_at": "2024-12-16T15:30:00Z"
}
```

**실패 응답 예시**

- 409 Conflict: 아이디 중복
```json
{
  "detail": "이미 사용 중인 아이디입니다."
}
```

- 422 Unprocessable Entity: 잘못된 요청 형식
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

- 500 Internal Server Error: 서버 오류
```json
{
  "detail": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
}
```

### 4.2 Pydantic 스키마 구조

#### SignUpRequest (요청)
- username: 아이디
- password: 비밀번호

#### UserResponse (응답)
- id: 사용자 ID
- username: 아이디
- created_at: 가입 일시

---

## 5. 보안 고려사항

### 5.1 비밀번호 보안

#### 5.1.1 해싱 알고리즘
- **bcrypt 사용**: 단방향 해시 함수로 원본 비밀번호 복구 불가
- **Salt 자동 생성**: bcrypt가 자동으로 랜덤 salt 생성 및 포함
- **Cost Factor 12**: 계산 비용 설정으로 무차별 대입 공격 방어

#### 5.1.2 저장 및 전송
- 평문 비밀번호는 메모리에서만 존재
- 데이터베이스에는 해싱된 값만 저장
- 로그에 비밀번호 기록 금지
- API 응답에 비밀번호 필드 제외

### 5.2 SQL Injection 방지
- SQLAlchemy ORM 사용으로 파라미터화된 쿼리 자동 처리
- 직접 SQL 작성 시 Prepared Statement 사용

### 5.3 타이밍 공격 방지
- 아이디 중복 확인 시 일정한 응답 시간 유지 고려
- 에러 메시지에서 정보 유출 최소화

---

## 6. 예외 처리

### 6.1 처리해야 할 예외 상황

| 상황 | HTTP 코드 | 메시지 |
|------|-----------|--------|
| 아이디 중복 | 409 | 이미 사용 중인 아이디입니다. |
| 필수 필드 누락 | 422 | 필수 입력값이 누락되었습니다. |
| 데이터베이스 오류 | 500 | 서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요. |

### 6.2 에러 응답 일관성
- FastAPI의 HTTPException 활용
- 모든 에러는 `{"detail": "message"}` 형식으로 반환

---

## 7. 구현 순서

### 7.1 Phase 1: 데이터베이스 설정 및 연결
1. SQLAlchemy 설정
   - `app/database.py` 생성
   - SQLite 인메모리 연결 문자열 설정 (`sqlite:///:memory:`)
   - Engine 생성 및 SessionLocal 설정

2. FastAPI 앱 lifespan 설정
   - `app/main.py`에 lifespan 함수 추가
   - 앱 시작 시 DB 연결 확인
   - 앱 종료 시 정리 작업

3. 연결 테스트
   - 서버 실행 후 DB 연결 확인
   - 간단한 쿼리 실행 테스트

### 7.2 Phase 2: User 모델 정의 및 테이블 생성
1. 디렉토리 구조
   - `app/models/` 생성
   - `app/models/user.py` 생성

2. User 모델 정의
   - SQLAlchemy Base 클래스 상속
   - 컬럼 정의 (id, username, hashed_password, created_at, updated_at)
   - Unique 제약조건 설정

3. DDL 실행
   - lifespan에서 `Base.metadata.create_all()` 호출
   - 서버 시작 시 테이블 자동 생성 확인

### 7.3 Phase 3: 기본 CRUD 동작 확인
1. 세션 의존성 설정
   - `app/database.py`에 `get_db()` 함수 추가
   - FastAPI Depends로 주입 가능하도록 설정

2. 간단한 테스트 엔드포인트 작성
   - `GET /test/db` - DB 연결 확인
   - `POST /test/user` - 사용자 생성 테스트
   - `GET /test/users` - 사용자 조회 테스트

3. SQLAlchemy 기본 조회 확인
   - session.add() 테스트
   - session.query() 테스트
   - 중복 username 제약조건 확인

### 7.4 Phase 4: 보안 유틸리티 구현
1. 디렉토리 구조
   - `app/core/` 생성
   - `app/core/security.py` 생성

2. 비밀번호 해싱 유틸리티
   - bcrypt 설치 및 임포트
   - `hash_password()`: 비밀번호 해싱
   - `verify_password()`: 비밀번호 검증
   - 간단한 테스트로 동작 확인

### 7.5 Phase 5: Pydantic 스키마 정의
1. 디렉토리 구조
   - `app/schemas/` 생성
   - `app/schemas/user.py` 생성

2. 스키마 작성
   - `UserCreate`: 회원가입 요청 (username, password)
   - `UserResponse`: 응답 (id, username, created_at)
   - `model_config` 설정 (from_attributes=True)

### 7.6 Phase 6: 회원가입 API 구현
1. 디렉토리 구조
   - `app/api/v1/` 생성
   - `app/api/v1/auth.py` 생성

2. 회원가입 엔드포인트
   - `POST /api/v1/auth/signup`
   - 아이디 중복 확인
   - 비밀번호 해싱
   - DB 저장
   - UserResponse 반환

3. 예외 처리
   - 중복 아이디: 409 Conflict
   - 필수 필드 누락: 422 Unprocessable Entity
   - DB 오류: 500 Internal Server Error

4. main.py에 라우터 등록
   - `app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])`

### 7.7 Phase 7: 테스트 및 검증
1. 수동 테스트
   - Swagger UI에서 회원가입 테스트
   - 정상 케이스 확인
   - 중복 아이디 에러 확인
   - 응답에 비밀번호 미포함 확인

2. 자동화 테스트 (선택)
   - pytest 설정
   - 회원가입 API 테스트 작성
   - DB 저장 확인 테스트

---

## 8. 기술 스택 및 라이브러리

### 8.1 핵심 라이브러리
| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| FastAPI | 0.100+ | API 프레임워크 |
| SQLAlchemy | 2.0+ | ORM |
| SQLite | Built-in | 인메모리 데이터베이스 |
| Pydantic | 2.0+ | 데이터 검증 및 스키마 |
| bcrypt | 4.0+ | 비밀번호 해싱 |

### 8.2 추가 유틸리티
- `pytest`: 테스트 프레임워크
- `pytest-asyncio`: 비동기 테스트 지원

### 8.3 제외된 라이브러리
- `Alembic`: 마이그레이션 대신 앱 시작 시 DDL 실행
- `python-dotenv`: 환경 변수 최소화
- `PostgreSQL`: SQLite 인메모리로 대체

---

## 9. 데이터베이스 설정

### 9.1 SQLite 인메모리 DB
- 연결 문자열: `sqlite:///:memory:`
- 서버 시작 시 자동으로 테이블 생성
- 서버 재시작 시 데이터 초기화 (인메모리 특성)

### 9.2 테이블 생성 시점
앱 시작 시 `lifespan` 이벤트에서 처리:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작: 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 필요시 초기 데이터 삽입
    # await seed_initial_data()

    yield

    # 종료: 정리 작업 (필요시)
```

### 9.3 초기 데이터 삽입 (선택)
테스트용 사용자나 관리자 계정이 필요한 경우:

```python
async def seed_initial_data():
    async with AsyncSession() as session:
        # 관리자 계정 생성 등
        pass
```

---

## 10. 마일스톤

| 단계 | 예상 작업 | 완료 조건 |
|------|-----------|-----------|
| Phase 1 | DB 설정 및 연결 | SQLite 인메모리 연결 확인, 서버 시작 성공 |
| Phase 2 | User 모델 및 테이블 생성 | DDL 실행 확인, 테이블 생성 확인 |
| Phase 3 | 기본 CRUD 동작 확인 | 테스트 엔드포인트로 생성/조회 성공 |
| Phase 4 | 보안 유틸리티 | bcrypt 해싱 동작 확인 |
| Phase 5 | Pydantic 스키마 | UserCreate, UserResponse 정의 완료 |
| Phase 6 | 회원가입 API | /api/v1/auth/signup 엔드포인트 동작 |
| Phase 7 | 테스트 및 검증 | Swagger UI에서 정상 동작 확인 |

---

**문서 버전**: 1.5
**작성일**: 2024-12-16
**수정일**: 2024-12-16
