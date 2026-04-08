from pathlib import Path
import runpy

import pytest
from flask import Flask

import conftest
from db import db


def test_postgres_container_success_path(monkeypatch):
    class FakePostgresContainer:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get_connection_url(self):
            return "postgresql://user:pass@localhost:5432/dbname"

    monkeypatch.setattr(conftest, "PostgresContainer", lambda *_args, **_kwargs: FakePostgresContainer())

    generator = conftest.postgres_container.__wrapped__()
    yielded_url = next(generator)

    assert yielded_url == "postgresql+psycopg2://user:pass@localhost:5432/dbname"

    with pytest.raises(StopIteration):
        next(generator)


def test_postgres_container_fallback_path(monkeypatch):
    def failing_container(*_args, **_kwargs):
        raise RuntimeError("container unavailable")

    monkeypatch.setattr(conftest, "PostgresContainer", failing_container)

    generator = conftest.postgres_container.__wrapped__()
    yielded_url = next(generator)

    expected_path = Path(conftest.__file__).resolve().parent / "test.db"
    assert yielded_url == f"sqlite:///{expected_path}"

    with pytest.raises(StopIteration):
        next(generator)


def test_main_module_entrypoint_calls_create_all_and_run(monkeypatch):
    calls = {"create_all": 0, "run": 0}

    def fake_create_all():
        calls["create_all"] += 1

    def fake_run(self, *args, **kwargs):
        calls["run"] += 1

    monkeypatch.setattr(db, "create_all", fake_create_all)
    monkeypatch.setattr(Flask, "run", fake_run)
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

    runpy.run_module("main", run_name="__main__")

    assert calls["create_all"] == 1
    assert calls["run"] == 1
