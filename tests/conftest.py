import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from plpipeline2627.models import Base

TEST_DATABASE_URL = os.environ.get(
    "PLP2627_TEST_DATABASE_URL",
    "postgresql+psycopg://localhost:5432/plpipeline2627_test",
)


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.execute(
        text(
            "TRUNCATE match, odds_quote, match_staging, odds_quote_staging "
            "RESTART IDENTITY CASCADE"
        )
    )
    session.commit()
    session.close()


@pytest.fixture()
def sample_csv_bytes() -> bytes:
    path = Path(__file__).parent / "fixtures" / "sample_2627.csv"
    return path.read_bytes()