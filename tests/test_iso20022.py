from decimal import Decimal
from pathlib import Path

import pytest

from finevalkit.iso20022 import evaluate_payment_controls, parse_pacs008

ROOT = Path(__file__).resolve().parents[1]
MESSAGE = ROOT / "data" / "iso20022" / "pacs008_valid.xml"


def test_parse_pacs008_and_apply_authorization_boundary():
    transfer = parse_pacs008(MESSAGE)
    allowed = evaluate_payment_controls(
        transfer, authorization_present=True, confirmation_present=True
    )
    blocked = evaluate_payment_controls(
        transfer, authorization_present=False, confirmation_present=False
    )

    assert transfer.amount == Decimal("50000.00")
    assert allowed["passed"] is True
    assert blocked["passed"] is False
    assert blocked["reasons"] == ["missing_authorization", "missing_confirmation"]


def test_parser_rejects_dtd(tmp_path):
    malicious = tmp_path / "message.xml"
    malicious.write_text("<!DOCTYPE x><Document/>", encoding="utf-8")
    with pytest.raises(ValueError, match="DTD"):
        parse_pacs008(malicious)
