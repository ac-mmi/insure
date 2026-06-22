"""Load demo policy, member, and coverage rules for API testing."""

from decimal import Decimal

from app.db.database import SessionLocal, init_db
from app.models.coverage_rule import CoverageRule
from app.models.member import Member
from app.models.policy import Policy


def seed_demo_data() -> dict:
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(Policy).filter(Policy.name == "Gold PPO 2026").first()
        if existing:
            member = db.query(Member).filter(Member.policy_id == existing.id).first()
            return {
                "policy_id": str(existing.id),
                "member_id": str(member.id) if member else None,
                "message": "Demo data already exists",
            }

        policy = Policy(
            name="Gold PPO 2026",
            deductible=Decimal("1000.00"),
            coverage_percentage=Decimal("0.80"),
            annual_limit=Decimal("10000.00"),
        )
        db.add(policy)
        db.flush()

        rules = [
            CoverageRule(
                policy_id=policy.id,
                service_code="99213",
                description="Office visit — established patient",
                is_covered=True,
            ),
            CoverageRule(
                policy_id=policy.id,
                service_code="92004",
                description="Vision exam",
                is_covered=True,
                coverage_percentage_override=Decimal("0.90"),
            ),
            CoverageRule(
                policy_id=policy.id,
                service_code="D2750",
                description="Dental crown",
                is_covered=False,
            ),
        ]
        db.add_all(rules)

        member = Member(
            name="Jane Doe",
            policy_id=policy.id,
            deductible_met=Decimal("1000.00"),
            amount_paid_ytd=Decimal("0.00"),
        )
        db.add(member)
        db.commit()
        db.refresh(policy)
        db.refresh(member)

        return {
            "policy_id": str(policy.id),
            "member_id": str(member.id),
            "message": "Demo data created",
        }
    finally:
        db.close()


if __name__ == "__main__":
    result = seed_demo_data()
    print(result)
