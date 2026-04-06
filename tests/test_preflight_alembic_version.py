from __future__ import annotations

from dataclasses import dataclass

from app.scripts import preflight_alembic_version as preflight


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _FirstResult:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


@dataclass
class _FakeConnection:
    should_exist: bool
    column_row: tuple[str, str, int | None] | None

    def __post_init__(self) -> None:
        self.executed_sql: list[str] = []
        self.params: list[dict | None] = []

    def execute(self, statement, params=None):
        sql = str(statement)
        self.executed_sql.append(sql)
        self.params.append(params)

        if "to_regclass('alembic_version')" in sql:
            return _ScalarResult("alembic_version" if self.should_exist else None)

        if "FROM information_schema.columns" in sql:
            return _FirstResult(self.column_row)

        return _ScalarResult(None)


class _BeginContext:
    def __init__(self, conn: _FakeConnection):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeEngine:
    def __init__(self, conn: _FakeConnection):
        self.conn = conn

    def begin(self):
        return _BeginContext(self.conn)


class _Settings:
    def sqlalchemy_database_url(self) -> str:
        return "postgresql+psycopg://user:pass@host/db"


def test_is_too_narrow_handles_expected_column_types():
    assert preflight._is_too_narrow("character varying", 32)
    assert preflight._is_too_narrow("varchar", 64)
    assert not preflight._is_too_narrow("character varying", 255)
    assert not preflight._is_too_narrow("text", None)


def test_main_alters_visible_schema_when_column_is_too_narrow(monkeypatch):
    conn = _FakeConnection(
        should_exist=True,
        column_row=("custom_schema", "character varying", 32),
    )

    monkeypatch.setattr(preflight, "get_settings", lambda: _Settings())
    monkeypatch.setattr(preflight, "create_engine", lambda *_args, **_kwargs: _FakeEngine(conn))

    preflight.main()

    assert any("ALTER TABLE %I.alembic_version" in sql for sql in conn.executed_sql)
    assert {"schema_name": "custom_schema"} in conn.params


def test_main_skips_alter_when_column_width_is_sufficient(monkeypatch):
    conn = _FakeConnection(
        should_exist=True,
        column_row=("public", "character varying", 255),
    )

    monkeypatch.setattr(preflight, "get_settings", lambda: _Settings())
    monkeypatch.setattr(preflight, "create_engine", lambda *_args, **_kwargs: _FakeEngine(conn))

    preflight.main()

    assert not any("ALTER TABLE %I.alembic_version" in sql for sql in conn.executed_sql)
