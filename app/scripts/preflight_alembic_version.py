from sqlalchemy import create_engine, text

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.sqlalchemy_database_url(), future=True)

    with engine.begin() as conn:
        exists = conn.execute(text("SELECT to_regclass('public.alembic_version')")).scalar()
        if not exists:
            return

        col = conn.execute(
            text(
                """
                SELECT data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'alembic_version'
                  AND column_name = 'version_num'
                """
            )
        ).first()
        if col is None:
            return

        data_type, max_len = col
        if data_type == "character varying" and max_len is not None and max_len < 255:
            conn.execute(
                text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")
            )


if __name__ == "__main__":
    main()
