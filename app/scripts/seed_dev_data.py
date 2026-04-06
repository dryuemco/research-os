import argparse

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.demo_seed_service import DemoSeedService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap deterministic demo data for pilot walkthroughs."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required safety switch to run seed/bootstrap mutations.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset previously seeded demo profile/matches/notifications and reload.",
    )
    parser.add_argument(
        "--no-proposal",
        action="store_true",
        help="Skip creating a demo proposal workspace from a shortlisted opportunity.",
    )
    parser.add_argument(
        "--fixture-path",
        default=get_settings().operational_source_fixture_path,
        help="Path to fixture JSON with records[] for ingestion.",
    )
    args = parser.parse_args()

    if not args.confirm:
        raise SystemExit("Refusing to run without --confirm (explicit invocation required).")

    session = SessionLocal()
    try:
        result = DemoSeedService(session).bootstrap(
            fixture_path=args.fixture_path,
            reset_demo_state=args.reset,
            create_demo_proposal=not args.no_proposal,
        )
        session.commit()
        print(
            "Demo bootstrap complete "
            f"(opportunities_loaded={result.opportunities_loaded}, "
            f"matches={result.matches_created}, notifications={result.notifications_created}, "
            f"proposal_created={result.proposal_created})"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
