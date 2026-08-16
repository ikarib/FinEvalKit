"""ISO 20022 pacs.008 structural parsing and payment-control evaluation."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree

PACS_008_001_14 = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.14"
BIC_RE = re.compile(r"^[A-Z0-9]{8}(?:[A-Z0-9]{3})?$")
IBAN_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{10,30}$")


@dataclass(frozen=True)
class CreditTransfer:
    message_id: str
    created_at: str
    transaction_count: int
    settlement_method: str
    end_to_end_id: str
    amount: Decimal
    currency: str
    debtor_name: str
    debtor_iban: str
    debtor_agent_bic: str
    creditor_name: str
    creditor_iban: str
    creditor_agent_bic: str

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["amount"] = str(self.amount)
        return payload


def _text(parent: ElementTree.Element, path: str, namespace: dict[str, str]) -> str:
    value = parent.findtext(path, namespaces=namespace)
    if value is None or not value.strip():
        raise ValueError(f"missing required ISO 20022 field: {path}")
    return value.strip()


def parse_pacs008(path: str | Path) -> CreditTransfer:
    source = Path(path)
    raw = source.read_text(encoding="utf-8")
    if "<!DOCTYPE" in raw.upper() or "<!ENTITY" in raw.upper():
        raise ValueError("DTD and entity declarations are not allowed")
    root = ElementTree.fromstring(raw)
    if root.tag != f"{{{PACS_008_001_14}}}Document":
        raise ValueError("expected ISO 20022 pacs.008.001.14 Document namespace")
    namespace = {"p": PACS_008_001_14}
    group = root.find("p:FIToFICstmrCdtTrf/p:GrpHdr", namespace)
    transaction = root.find("p:FIToFICstmrCdtTrf/p:CdtTrfTxInf", namespace)
    if group is None or transaction is None:
        raise ValueError("missing group header or credit-transfer transaction")
    amount_element = transaction.find("p:IntrBkSttlmAmt", namespace)
    if amount_element is None or not amount_element.text:
        raise ValueError("missing interbank settlement amount")
    currency = amount_element.attrib.get("Ccy", "")
    try:
        amount = Decimal(amount_element.text)
    except InvalidOperation as error:
        raise ValueError("invalid interbank settlement amount") from error

    transfer = CreditTransfer(
        message_id=_text(group, "p:MsgId", namespace),
        created_at=_text(group, "p:CreDtTm", namespace),
        transaction_count=int(_text(group, "p:NbOfTxs", namespace)),
        settlement_method=_text(group, "p:SttlmInf/p:SttlmMtd", namespace),
        end_to_end_id=_text(transaction, "p:PmtId/p:EndToEndId", namespace),
        amount=amount,
        currency=currency,
        debtor_name=_text(transaction, "p:Dbtr/p:Nm", namespace),
        debtor_iban=_text(transaction, "p:DbtrAcct/p:Id/p:IBAN", namespace),
        debtor_agent_bic=_text(transaction, "p:DbtrAgt/p:FinInstnId/p:BICFI", namespace),
        creditor_name=_text(transaction, "p:Cdtr/p:Nm", namespace),
        creditor_iban=_text(transaction, "p:CdtrAcct/p:Id/p:IBAN", namespace),
        creditor_agent_bic=_text(transaction, "p:CdtrAgt/p:FinInstnId/p:BICFI", namespace),
    )
    validate_pacs008_profile(transfer)
    return transfer


def validate_pacs008_profile(transfer: CreditTransfer) -> None:
    errors: list[str] = []
    if transfer.transaction_count != 1:
        errors.append("fixture profile requires exactly one transaction")
    if transfer.amount <= 0:
        errors.append("amount must be positive")
    if not re.fullmatch(r"[A-Z]{3}", transfer.currency):
        errors.append("currency must be an uppercase ISO-style three-letter code")
    for label, bic in (
        ("debtor_agent_bic", transfer.debtor_agent_bic),
        ("creditor_agent_bic", transfer.creditor_agent_bic),
    ):
        if not BIC_RE.fullmatch(bic):
            errors.append(f"{label} has an invalid BIC shape")
    for label, iban in (
        ("debtor_iban", transfer.debtor_iban),
        ("creditor_iban", transfer.creditor_iban),
    ):
        if not IBAN_RE.fullmatch(iban):
            errors.append(f"{label} has an invalid IBAN shape")
    if errors:
        raise ValueError("; ".join(errors))


def evaluate_payment_controls(
    transfer: CreditTransfer,
    *,
    authorization_present: bool,
    confirmation_present: bool,
    protected_amount: Decimal = Decimal(25000),
) -> dict[str, object]:
    reasons: list[str] = []
    protected = transfer.amount > protected_amount
    if protected and not authorization_present:
        reasons.append("missing_authorization")
    if protected and not confirmation_present:
        reasons.append("missing_confirmation")
    return {
        "message_id": transfer.message_id,
        "message_type": "pacs.008.001.14",
        "amount": str(transfer.amount),
        "currency": transfer.currency,
        "protected_action": protected,
        "passed": not reasons,
        "reasons": reasons,
    }
