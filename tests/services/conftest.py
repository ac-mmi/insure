from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from tests.fixtures.domain import create_member, create_policy


@pytest.fixture
def standard_policy(db_session: Session):
    return create_policy(db_session)


@pytest.fixture
def member_deductible_met(db_session: Session, standard_policy):
    return create_member(
        db_session,
        policy=standard_policy,
        deductible_met=Decimal("1000.00"),
    )


@pytest.fixture
def member_deductible_not_met(db_session: Session, standard_policy):
    return create_member(
        db_session,
        policy=standard_policy,
        deductible_met=Decimal("0.00"),
    )


@pytest.fixture
def member_near_annual_limit(db_session: Session, standard_policy):
    return create_member(
        db_session,
        policy=standard_policy,
        deductible_met=Decimal("1000.00"),
        amount_paid_ytd=Decimal("9500.00"),
    )
