"""SEC Company Facts ingestion with filing-level provenance."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class XBRLFact:
    taxonomy: str
    concept: str
    label: str
    unit: str
    value: Decimal
    start: str | None
    end: str
    form: str
    fiscal_year: int | None
    fiscal_period: str | None
    accession: str
    filed: str
    filing_url: str | None = None

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.concept, self.end, self.unit)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["value"] = str(self.value)
        return payload


def load_companyfacts(
    path: str | Path,
    *,
    forms: tuple[str, ...] = ("10-K",),
    concepts: set[str] | None = None,
) -> list[XBRLFact]:
    """Load facts from SEC Company Facts JSON or a reduced compatible fixture."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    facts: list[XBRLFact] = []
    for taxonomy, taxonomy_facts in payload.get("facts", {}).items():
        for concept, concept_payload in taxonomy_facts.items():
            if concepts is not None and concept not in concepts:
                continue
            for unit, observations in concept_payload.get("units", {}).items():
                for observation in observations:
                    if observation.get("form") not in forms:
                        continue
                    facts.append(
                        XBRLFact(
                            taxonomy=taxonomy,
                            concept=concept,
                            label=concept_payload.get("label", concept),
                            unit=unit,
                            value=Decimal(str(observation["val"])),
                            start=observation.get("start"),
                            end=observation["end"],
                            form=observation["form"],
                            fiscal_year=observation.get("fy"),
                            fiscal_period=observation.get("fp"),
                            accession=observation.get("accn", ""),
                            filed=observation.get("filed", ""),
                            filing_url=observation.get("filing_url"),
                        )
                    )
    return sorted(facts, key=lambda fact: (fact.concept, fact.end, fact.filed))


def latest_facts(facts: list[XBRLFact]) -> dict[tuple[str, str, str], XBRLFact]:
    """Deduplicate amendments/restatements by the latest filed observation."""

    selected: dict[tuple[str, str, str], XBRLFact] = {}
    for fact in facts:
        current = selected.get(fact.key)
        if current is None or fact.filed >= current.filed:
            selected[fact.key] = fact
    return selected
