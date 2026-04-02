from app.db.session import SessionLocal
from app.domain.common.enums import UserRole
from app.domain.identity_models import User
from app.domain.opportunity_discovery.models import InterestProfile
from app.services.operational_loop_service import OperationalLoopService


def _seed_user(session) -> User:
    user = session.query(User).filter(User.email == "pilot-admin@example.org").first()
    if user is None:
        user = User(
            email="pilot-admin@example.org",
            display_name="Pilot Admin",
            role=UserRole.ADMIN,
            team_name="grant-office",
            org_name="rpos-internal",
            is_active=True,
        )
        session.add(user)
        session.flush()
    return user


def _seed_user(session) -> User:
    user = session.query(User).filter(User.email == "pilot-admin@example.org").first()
    if user is None:
        user = User(
            email="pilot-admin@example.org",
            display_name="Pilot Admin",
            role=UserRole.ADMIN,
            team_name="grant-office",
            org_name="rpos-internal",
            is_active=True,
        )
        session.add(user)
        session.flush()
    return user


def main() -> None:
    session = SessionLocal()
    try:
        user = _seed_user(session)
        profile = (
            session.query(InterestProfile)
            .filter(InterestProfile.name == "Default Dev Profile")
            .first()
        )
        if profile is None:
            session.add(
                InterestProfile(
                    user_id=user.id,
                    name="Default Dev Profile",
                    parameters_json={
                        "allowed_programs": ["Horizon Europe", "Erasmus+"],
                        "preferred_keywords": ["ai", "climate", "health"],
                        "weights": {"keyword_overlap": 0.7, "budget_fit": 0.3},
                    },
                )
            )
        OperationalLoopService(session).ensure_default_jobs()
        session.commit()
        print(f"Seeded pilot user id={user.id}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
