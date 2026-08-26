from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from plpipeline2627.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)


def get_session() -> Session:
    return SessionLocal()