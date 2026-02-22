-- =============================================================================
-- Announce-Go API — PostgreSQL DDL
-- =============================================================================
-- 설계 원칙:
--   - DB-level FK 제약 미사용 (애플리케이션 레벨에서 참조 무결성 관리)
--   - 참조 관계는 컬럼 주석(ref: table.column)으로 명시
--   - ENUM: PostgreSQL 네이티브 ENUM 타입 사용
--   - JSONB: agencies.categories는 JSONB (인덱싱 가능)
--   - updated_at: 트리거로 자동 갱신
-- =============================================================================


-- =============================================================================
-- ENUM 타입
-- =============================================================================

-- 사용자 역할
CREATE TYPE user_role AS ENUM (
    'ADMIN',        -- 최고 관리자
    'AGENCY',       -- 대행사
    'ADVERTISER'    -- 광고주
);

-- 승인 상태
CREATE TYPE approval_status AS ENUM (
    'PENDING',      -- 승인 대기
    'APPROVED',     -- 승인 완료
    'REJECTED'      -- 거절
);

-- 순위 추적 유형
CREATE TYPE rank_type AS ENUM (
    'PLACE',        -- 플레이스 순위
    'CAFE',         -- 카페 글 순위
    'BLOG'          -- 블로그 글 순위
);

-- 추적 상태
CREATE TYPE tracking_status AS ENUM (
    'ACTIVE',       -- 추적 중
    'STOPPED'       -- 추적 중단
);


-- =============================================================================
-- updated_at 자동 갱신 트리거 함수
-- =============================================================================

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- 테이블 정의
-- =============================================================================

-- -----------------------------------------------------------------------------
-- files: 업로드 파일 정보
-- -----------------------------------------------------------------------------
CREATE TABLE files (
    id                BIGSERIAL    PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,               -- 원본 파일명
    stored_filename   VARCHAR(255) NOT NULL,               -- 저장된 파일명
    file_type         VARCHAR(50)  NOT NULL,               -- 파일 유형 (business_license | logo | other)
    mime_type         VARCHAR(100) NOT NULL,               -- MIME 타입
    storage_path      VARCHAR(500) NOT NULL UNIQUE,        -- 스토리지 경로 (S3 key 또는 로컬 경로)
    file_size         BIGINT       NOT NULL,               -- 파일 크기 (bytes)
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- storage_path: UNIQUE 제약이 묵시적 인덱스를 생성하므로 별도 인덱스 불필요
-- (모델의 index=True 반영)
CREATE INDEX idx_files_storage_path ON files (storage_path);

CREATE TRIGGER trg_files_updated_at
    BEFORE UPDATE ON files
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMENT ON TABLE files IS '업로드된 파일 정보 (사업자등록증, 로고 등)';
COMMENT ON COLUMN files.file_type IS '파일 유형: business_license | logo | other';
COMMENT ON COLUMN files.storage_path IS '스토리지 저장 경로 (UNIQUE). S3 key 또는 로컬 경로';
COMMENT ON COLUMN files.file_size IS '파일 크기 (bytes)';


-- -----------------------------------------------------------------------------
-- users: 사용자 (admin / agency / advertiser)
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id              BIGSERIAL       PRIMARY KEY,
    login_id        VARCHAR(50)     NOT NULL UNIQUE,       -- 로그인 ID (고유)
    email           VARCHAR(255)    NOT NULL UNIQUE,       -- 이메일 (고유)
    password_hash   VARCHAR(255)    NOT NULL,              -- 비밀번호 해시
    name            VARCHAR(100)    NOT NULL,              -- 이름
    phone           VARCHAR(20)     NULL,                  -- 전화번호
    company_name    VARCHAR(100)    NULL,                  -- 회사명
    role            user_role       NOT NULL DEFAULT 'ADVERTISER', -- 역할
    approval_status approval_status NOT NULL DEFAULT 'PENDING',    -- 승인 상태
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- login_id, email: UNIQUE 제약이 묵시적 인덱스를 생성하므로 별도 인덱스 불필요
-- (모델의 index=True 반영)
CREATE INDEX idx_users_login_id ON users (login_id);
CREATE INDEX idx_users_email    ON users (email);

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMENT ON TABLE users IS '사용자 (admin / agency / advertiser). admin은 초기 데이터로 생성';
COMMENT ON COLUMN users.login_id IS '로그인 ID (UNIQUE)';
COMMENT ON COLUMN users.role IS 'admin: 최고 관리자, agency: 대행사, advertiser: 광고주';
COMMENT ON COLUMN users.approval_status IS 'pending: 승인 대기, approved: 승인 완료, rejected: 거절';


-- -----------------------------------------------------------------------------
-- advertisers: 광고주 프로필 (PK = users.id, 1:1)
-- -----------------------------------------------------------------------------
CREATE TABLE advertisers (
    id                       BIGINT      PRIMARY KEY,      -- ref: users.id
    business_license_file_id BIGINT      NULL,             -- ref: files.id (사업자등록증)
    logo_file_id             BIGINT      NULL,             -- ref: files.id (로고)
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_advertisers_updated_at
    BEFORE UPDATE ON advertisers
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMENT ON TABLE advertisers IS '광고주 프로필. id = users.id (1:1 관계, FK 제약 없음)';
COMMENT ON COLUMN advertisers.id IS 'ref: users.id — autoincrement 없이 users.id를 그대로 사용';
COMMENT ON COLUMN advertisers.business_license_file_id IS 'ref: files.id — 사업자등록증 파일';
COMMENT ON COLUMN advertisers.logo_file_id IS 'ref: files.id — 로고 파일';


-- -----------------------------------------------------------------------------
-- agencies: 대행사 프로필 (PK = users.id, 1:1)
-- -----------------------------------------------------------------------------
CREATE TABLE agencies (
    id         BIGINT      PRIMARY KEY,                    -- ref: users.id
    categories JSONB       NOT NULL DEFAULT '[]'::JSONB,   -- 담당 카테고리 배열
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_agencies_updated_at
    BEFORE UPDATE ON agencies
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMENT ON TABLE agencies IS '대행사 프로필. id = users.id (1:1 관계, FK 제약 없음)';
COMMENT ON COLUMN agencies.id IS 'ref: users.id — autoincrement 없이 users.id를 그대로 사용';
COMMENT ON COLUMN agencies.categories IS '담당 카테고리 배열 (JSONB). '
    '가능한 값: place_rank, cafe_rank, blog_rank, blog_posting, news_article, cafe_infiltration';


-- -----------------------------------------------------------------------------
-- agency_advertiser_mappings: 대행사-광고주 매핑 (복합 PK)
-- -----------------------------------------------------------------------------
CREATE TABLE agency_advertiser_mappings (
    agency_id     BIGINT      NOT NULL,                    -- ref: agencies.id
    advertiser_id BIGINT      NOT NULL,                    -- ref: advertisers.id
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (agency_id, advertiser_id)
);

-- 복합 PK 인덱스가 agency_id 선두 컬럼을 커버하나, 모델의 index=True 반영
CREATE INDEX idx_agency_advertiser_mappings_agency_id     ON agency_advertiser_mappings (agency_id);
-- advertiser_id 단독 역방향 조회를 위한 인덱스
CREATE INDEX idx_agency_advertiser_mappings_advertiser_id ON agency_advertiser_mappings (advertiser_id);

CREATE TRIGGER trg_agency_advertiser_mappings_updated_at
    BEFORE UPDATE ON agency_advertiser_mappings
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMENT ON TABLE agency_advertiser_mappings IS '대행사-광고주 매핑 (다대다, FK 제약 없음)';
COMMENT ON COLUMN agency_advertiser_mappings.agency_id IS 'ref: agencies.id';
COMMENT ON COLUMN agency_advertiser_mappings.advertiser_id IS 'ref: advertisers.id';


-- -----------------------------------------------------------------------------
-- rank_trackings: 순위 추적 설정
-- -----------------------------------------------------------------------------
CREATE TABLE rank_trackings (
    id              BIGSERIAL       PRIMARY KEY,
    type            rank_type       NOT NULL,              -- 순위 유형 (place | cafe | blog)
    agency_id       BIGINT          NOT NULL,              -- ref: agencies.id
    advertiser_id   BIGINT          NOT NULL,              -- ref: advertisers.id
    keyword         VARCHAR(255)    NOT NULL,              -- 추적 키워드
    url             TEXT            NOT NULL,              -- 추적 URL
    status          tracking_status NOT NULL DEFAULT 'ACTIVE', -- 추적 상태
    current_session INT             NOT NULL DEFAULT 1,    -- 현재 회차 (배치 로직 상태값)
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rank_trackings_type          ON rank_trackings (type);
CREATE INDEX idx_rank_trackings_agency_id     ON rank_trackings (agency_id);
CREATE INDEX idx_rank_trackings_advertiser_id ON rank_trackings (advertiser_id);
CREATE INDEX idx_rank_trackings_status        ON rank_trackings (status);

CREATE TRIGGER trg_rank_trackings_updated_at
    BEFORE UPDATE ON rank_trackings
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMENT ON TABLE rank_trackings IS '순위 추적 설정. agency가 등록하고 advertiser에게 공개';
COMMENT ON COLUMN rank_trackings.type IS 'ref: rank_type ENUM — place: 플레이스, cafe: 카페, blog: 블로그';
COMMENT ON COLUMN rank_trackings.agency_id IS 'ref: agencies.id';
COMMENT ON COLUMN rank_trackings.advertiser_id IS 'ref: advertisers.id';
COMMENT ON COLUMN rank_trackings.current_session IS '현재 회차 번호 (배치 상태값). 크롤러가 관리';


-- -----------------------------------------------------------------------------
-- rank_histories: 순위 추적 결과 히스토리 (TimestampMixin 없음)
-- -----------------------------------------------------------------------------
CREATE TABLE rank_histories (
    id             BIGSERIAL   PRIMARY KEY,
    tracking_id    BIGINT      NOT NULL,                   -- ref: rank_trackings.id
    rank           INT         NULL,                       -- 순위 (NULL = 해당 회차 미노출)
    session_number INT         NOT NULL DEFAULT 1,         -- 회차 번호
    checked_at     TIMESTAMPTZ NOT NULL                    -- 체크 일시 (크롤러가 기록)
);

CREATE INDEX idx_rank_histories_tracking_id ON rank_histories (tracking_id);

COMMENT ON TABLE rank_histories IS '일일 크롤링 순위 결과. created_at/updated_at 없음';
COMMENT ON COLUMN rank_histories.tracking_id IS 'ref: rank_trackings.id';
COMMENT ON COLUMN rank_histories.rank IS '순위. NULL이면 해당 회차에서 미노출';
COMMENT ON COLUMN rank_histories.session_number IS '회차 번호 (rank_trackings.current_session 기준)';
COMMENT ON COLUMN rank_histories.checked_at IS '크롤러가 순위를 확인한 일시';


-- -----------------------------------------------------------------------------
-- blog_postings: 블로그 포스팅 작업 기록
-- -----------------------------------------------------------------------------
CREATE TABLE blog_postings (
    id            BIGSERIAL    PRIMARY KEY,
    agency_id     BIGINT       NOT NULL,                   -- ref: agencies.id
    advertiser_id BIGINT       NOT NULL,                   -- ref: advertisers.id
    keyword       VARCHAR(255) NOT NULL,                   -- 포스팅 키워드
    url           TEXT         NOT NULL,                   -- 포스팅 URL
    posting_date  DATE         NOT NULL,                   -- 포스팅 날짜
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_blog_postings_agency_id     ON blog_postings (agency_id);
CREATE INDEX idx_blog_postings_advertiser_id ON blog_postings (advertiser_id);
CREATE INDEX idx_blog_postings_posting_date  ON blog_postings (posting_date);

CREATE TRIGGER trg_blog_postings_updated_at
    BEFORE UPDATE ON blog_postings
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMENT ON TABLE blog_postings IS '블로그 포스팅 작업 기록. agency가 등록, advertiser는 읽기 전용';
COMMENT ON COLUMN blog_postings.agency_id IS 'ref: agencies.id';
COMMENT ON COLUMN blog_postings.advertiser_id IS 'ref: advertisers.id';


-- -----------------------------------------------------------------------------
-- cafe_infiltrations: 카페 침투 작업 기록
-- -----------------------------------------------------------------------------
CREATE TABLE cafe_infiltrations (
    id                BIGSERIAL    PRIMARY KEY,
    advertiser_id     BIGINT       NOT NULL,               -- ref: advertisers.id
    infiltration_date DATE         NOT NULL,               -- 침투 날짜
    title             VARCHAR(500) NOT NULL,               -- 게시글 제목
    content           TEXT         NULL,                   -- 게시글 내용
    cafe_name         VARCHAR(255) NULL,                   -- 카페명
    url               TEXT         NULL,                   -- 게시글 URL
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cafe_infiltrations_advertiser_id     ON cafe_infiltrations (advertiser_id);
CREATE INDEX idx_cafe_infiltrations_infiltration_date ON cafe_infiltrations (infiltration_date);

CREATE TRIGGER trg_cafe_infiltrations_updated_at
    BEFORE UPDATE ON cafe_infiltrations
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMENT ON TABLE cafe_infiltrations IS '카페 침투 작업 기록. admin이 등록, agency/advertiser는 읽기 전용';
COMMENT ON COLUMN cafe_infiltrations.advertiser_id IS 'ref: advertisers.id';
COMMENT ON COLUMN cafe_infiltrations.infiltration_date IS '카페 게시글 작성 날짜';


-- -----------------------------------------------------------------------------
-- press_articles: 언론 기사 작업 기록
-- -----------------------------------------------------------------------------
CREATE TABLE press_articles (
    id            BIGSERIAL    PRIMARY KEY,
    advertiser_id BIGINT       NOT NULL,                   -- ref: advertisers.id
    article_date  DATE         NOT NULL,                   -- 기사 날짜
    title         VARCHAR(500) NOT NULL,                   -- 기사 제목
    content       TEXT         NULL,                       -- 기사 내용
    url           TEXT         NULL,                       -- 기사 URL
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_press_articles_advertiser_id ON press_articles (advertiser_id);
CREATE INDEX idx_press_articles_article_date  ON press_articles (article_date);

CREATE TRIGGER trg_press_articles_updated_at
    BEFORE UPDATE ON press_articles
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

COMMENT ON TABLE press_articles IS '언론 기사 작업 기록. admin이 등록, agency/advertiser는 읽기 전용';
COMMENT ON COLUMN press_articles.advertiser_id IS 'ref: advertisers.id';
COMMENT ON COLUMN press_articles.article_date IS '기사 게재 날짜';
