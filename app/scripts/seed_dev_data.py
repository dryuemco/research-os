from app.db.session import SessionLocal
from app.domain.opportunity_discovery.models import InterestProfile


def main() -> None:
    session = SessionLocal()
    try:
        profile = (
            session.query(InterestProfile)
            .filter(InterestProfile.name == "Default Dev Profile")
            .first()
        )
        if profile is None:
            session.add(
                InterestProfile(
                    user_id="dev-user",
                    name="Default Dev Profile",
                    parameters_json={
                        "allowed_programs": ["Horizon Europe", "Erasmus+"],
                        "preferred_keywords": ["ai", "climate", "health"],
                        "weights": {"keyword_overlap": 0.7, "budget_fit": 0.3},
                    },
                )
            )
            session.commit()
            print("Seeded default dev interest profile")
        else:
            print("Dev profile already present")
    finally:
        session.close()


if __name__ == "__main__":
    main()
