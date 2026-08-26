FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/

RUN pip install --no-cache-dir .

CMD ["plp2627", "run", "--season", "2627"]