"""Claim rollup — claim status derived from line item outcomes."""

import pytest

from app.models.claim_line_item import ClaimLineItem
from app.models.enums import ClaimLineItemStatus, ClaimStatus
from app.services.adjudication import AdjudicationError, rollup_claim_status


class TestClaimRollupLogic:
    def test_all_lines_approved_yields_claim_approved(self):
        line_items = [
            ClaimLineItem(status=ClaimLineItemStatus.APPROVED),
            ClaimLineItem(status=ClaimLineItemStatus.APPROVED),
        ]

        assert rollup_claim_status(line_items) == ClaimStatus.APPROVED

    def test_all_lines_denied_yields_claim_denied(self):
        line_items = [
            ClaimLineItem(status=ClaimLineItemStatus.DENIED),
            ClaimLineItem(status=ClaimLineItemStatus.DENIED),
        ]

        assert rollup_claim_status(line_items) == ClaimStatus.DENIED

    def test_mixed_lines_yields_claim_partially_approved(self):
        line_items = [
            ClaimLineItem(status=ClaimLineItemStatus.APPROVED),
            ClaimLineItem(status=ClaimLineItemStatus.DENIED),
        ]

        assert rollup_claim_status(line_items) == ClaimStatus.PARTIALLY_APPROVED

    def test_single_approved_line_yields_claim_approved(self):
        line_items = [ClaimLineItem(status=ClaimLineItemStatus.APPROVED)]

        assert rollup_claim_status(line_items) == ClaimStatus.APPROVED

    def test_single_denied_line_yields_claim_denied(self):
        line_items = [ClaimLineItem(status=ClaimLineItemStatus.DENIED)]

        assert rollup_claim_status(line_items) == ClaimStatus.DENIED

    def test_pending_lines_are_not_valid_for_rollup(self):
        line_items = [
            ClaimLineItem(status=ClaimLineItemStatus.APPROVED),
            ClaimLineItem(status=ClaimLineItemStatus.PENDING),
        ]

        with pytest.raises(AdjudicationError):
            rollup_claim_status(line_items)
