from app.db.session import SessionLocal
from app.services.execution_runtime_service import ExecutionRuntimeService


def main() -> None:
    with SessionLocal() as session:
        service = ExecutionRuntimeService(session)
        processed = 0
        while service.process_next_job() is not None:
            processed += 1
        session.commit()
        print(f"processed_jobs={processed}")


if __name__ == "__main__":
    main()
