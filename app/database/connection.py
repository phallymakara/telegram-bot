from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL
from app.database.models import Base


connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}


engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db_session():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise