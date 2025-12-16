"""
SQLAlchemy 데이터베이스 설정
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite 인메모리 데이터베이스
DATABASE_URL = "sqlite:///:memory:"

# Engine 생성 (check_same_thread=False는 SQLite에서 필요)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionLocal 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성 (모든 모델이 상속할 클래스)
Base = declarative_base()


# 의존성: DB 세션 제공
def get_db():
    """
    FastAPI 의존성으로 사용할 DB 세션 제공
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
