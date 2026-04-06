from __future__ import annotations

import time

from app.core.config import get_settings
from app.db.session import session_scope
from app.services.operational_loop_service import OperationalLoopService


def main() -> None:
    settings = get_settings()
    if not settings.operational_scheduler_enabled:
        print("Operational scheduler disabled by configuration")
        return

    print("Starting operational loop worker")
    while True:
        with session_scope() as db:
            service = OperationalLoopService(db)
            service.ensure_default_jobs()
            runs = service.run_due_jobs()
            if runs:
                print(f"Processed {len(runs)} operational job(s)")
        time.sleep(settings.operational_scheduler_tick_seconds)


if __name__ == "__main__":
    main()
