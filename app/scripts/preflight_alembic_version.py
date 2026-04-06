from sqlalchemy import create_engine, text

from app.core.config import get_settings


MIN_ALEMBIC_VERSION_COLUMN_LEN = 255


def _is_too_narrow(data_type: str, max_len: int | None) -> bool:
    normalized = data_type.lower().strip()
    variable_char_types = {"character varying", "varchar", "character", "char", "bpchar"}
    return normalized in variable_char_types and max_len is not None and max_len < MIN_ALEMBIC_VERSION_COLUMN_LEN


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.sqlalchemy_database_url(), future=True)

    with engine.begin() as conn:
        exists = conn.execute(text("SELECT to_regclass('alembic_version')")).scalar()
        if not exists:
            return

        col = conn.execute(
            text(
                """
                SELECT table_schema, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'alembic_version'
                  AND column_name = 'version_num'
                ORDER BY (table_schema = current_schema()) DESC, table_schema ASC
                LIMIT 1
                """
            )
        ).first()
        if col is None:
            return

        table_schema, data_type, max_len = col
        if _is_too_narrow(data_type, max_len):
            conn.execute(
                text(
                    """
                    DO $$
                    DECLARE target_schema text := :schema_name;
                    BEGIN
                      EXECUTE format(
                        'ALTER TABLE %I.alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)',
                        target_schema
                      );
                    END $$;
                    """
                ),
                {"schema_name": table_schema},
            )


if __name__ == "__main__":
    main()
