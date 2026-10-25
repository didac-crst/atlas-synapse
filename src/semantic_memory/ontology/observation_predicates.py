"""Canonical governed proposals for typed Observation measurements.

These are proposal *payloads* for the existing ontology governance workflow.
They are not applied by migration or seed. Production install requires
propose → review → apply (or the same path under a mock reviewer in tests).

V1 model (one numeric measurement per Observation entity):

    Observation --observationOf--> Thing
    Observation --observationType--> string
    Observation --numericValue--> number
    Observation --unit--> string
    statement.observed_at / occurredAt for measurement time
    statement.asserted_at for import/acceptance time
"""

from __future__ import annotations

from typing import Any

from semantic_memory.models.enums import Cardinality, ValueKind

OBSERVATION_PREDICATE_PROPOSALS: tuple[dict[str, Any], ...] = (
    {
        "key": "observationOf",
        "label": "observation of",
        "description": (
            "Links an Observation to the Thing it observes (person, device, "
            "asset, place, or other entity). Asymmetric; not a synonym of relatedTo."
        ),
        "value_kind": ValueKind.ENTITY,
        "cardinality": Cardinality.MANY,
        "domain_keys": ["Observation"],
        "range_keys": ["Thing"],
        "is_symmetric": False,
        "is_transitive": False,
        "summary": "Propose predicate core:observationOf",
    },
    {
        "key": "observationType",
        "label": "observation type",
        "description": (
            "Semantic measurement kind for an Observation, as a canonical string "
            "(e.g. height, weight, temperature, power_draw). Not domain-specific "
            "class subclasses."
        ),
        "value_kind": ValueKind.STRING,
        "cardinality": Cardinality.ONE,
        "domain_keys": ["Observation"],
        "range_keys": [],
        "is_symmetric": False,
        "is_transitive": False,
        "summary": "Propose predicate core:observationType",
    },
    {
        "key": "numericValue",
        "label": "numeric value",
        "description": (
            "Typed numeric magnitude of an Observation. Stored as object_number so "
            "values are queryable without parsing description text."
        ),
        "value_kind": ValueKind.NUMBER,
        "cardinality": Cardinality.ONE,
        "domain_keys": ["Observation"],
        "range_keys": [],
        "is_symmetric": False,
        "is_transitive": False,
        "summary": "Propose predicate core:numericValue",
    },
    {
        "key": "unit",
        "label": "unit",
        "description": (
            "Unit of measure for numericValue as a canonical string "
            "(e.g. cm, kg, C, kWh). V1 does not introduce a units ontology."
        ),
        "value_kind": ValueKind.STRING,
        "cardinality": Cardinality.ONE,
        "domain_keys": ["Observation"],
        "range_keys": [],
        "is_symmetric": False,
        "is_transitive": False,
        "summary": "Propose predicate core:unit",
    },
)


def observation_predicate_keys() -> tuple[str, ...]:
    return tuple(str(item["key"]) for item in OBSERVATION_PREDICATE_PROPOSALS)
