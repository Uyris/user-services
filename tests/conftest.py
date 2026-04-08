# tests/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from main import app as flask_app
from main import create_app
from db import db
import os
from pathlib import Path

@pytest.fixture(scope="session")
def postgres_container():
    try:
        with PostgresContainer("postgres:15-alpine") as postgres:
            url = postgres.get_connection_url()

            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://")

            yield url
    except Exception:
        yield f"sqlite:///{Path(__file__).resolve().parent / 'test.db'}"

@pytest.fixture(scope="session")
def app(postgres_container):

    os.environ["SQLALCHEMY_DATABASE_URI"] = postgres_container
    
    flask_app = create_app()
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()