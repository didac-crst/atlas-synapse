"""Retrieval request/response schemas with transparent ranking signals."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from semantic_memory.models.enums import EntityStatus, StatementStatus
from semantic_memory.schemas.conflicts import ConflictResponse
from semantic_memory.schemas.entities import EntityResponse
from semantic_memory.schemas.memory_quality import QualityWarning
from semantic_memory.schemas.provenance import ExplainStatementResponse
from semantic_memory.schemas.statements import StatementResponse, TimelineResponse


class RankingSignals(BaseModel):
    """Transparent ranking inputs. Not a truth score."""

    lexical_relevance: float = 0.0
    temporal_validity: float = 0.0
    recency: float = 0.0
    evidence_presence: float = 0.0
    source_reliability: float = 0.0
    entity_proximity: float = 0.0
    ontology_specificity: float = 0.0
    notes: list[str] = Field(default_factory=list)

    @property
    def ranking_score(self) -> float:
        """Ordering aid only — never authoritative for truth or identity."""
        return (
            self.lexical_relevance * 0.30
            + self.temporal_validity * 0.15
            + self.recency * 0.15
            + self.evidence_presence * 0.10
            + self.source_reliability * 0.10
            + self.entity_proximity * 0.10
            + self.ontology_specificity * 0.10
        )


class RankedEntityHit(BaseModel):
    entity: EntityResponse
    signals: RankingSignals
    ranking_score: float
    match_reasons: list[str] = Field(default_factory=list)


class RankedStatementHit(BaseModel):
    statement: StatementResponse
    signals: RankingSignals
    ranking_score: float
    match_reasons: list[str] = Field(default_factory=list)


class SearchEntitiesRequest(BaseModel):
    query: str = Field(min_length=1)
    class_key: str | None = None
    namespace_key: str = "core"
    status: EntityStatus | None = EntityStatus.ACTIVE
    limit: int = Field(default=25, ge=1, le=100)
    as_of: datetime | None = None


class SearchEntitiesResponse(BaseModel):
    query: str
    hits: list[RankedEntityHit] = Field(default_factory=list)
    ranking_explanations: list[str] = Field(default_factory=list)


class TemporalState(StrEnum):
    """How statement validity bounds are populated (not a truth judgment).

    ``unbounded`` means both bounds are null (temporally unspecified), not
    "valid forever".
    """

    BOUNDED = "bounded"
    OPEN_END = "open_end"
    OPEN_START = "open_start"
    UNBOUNDED = "unbounded"


class SearchStatementsRequest(BaseModel):
    """Typed statement search. Unknown fields are rejected (extra=forbid)."""

    model_config = ConfigDict(extra="forbid")

    query: str | None = None
    subject_entity_id: uuid.UUID | None = None
    object_entity_id: uuid.UUID | None = None
    entity_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "Match statements where this entity is subject OR object. "
            "Do not combine with subject_entity_id/object_entity_id."
        ),
    )
    predicate_key: str | None = None
    namespace_key: str | None = Field(
        default=None,
        description=(
            "When set with predicate_key, scopes predicate resolution (default core). "
            "When set alone, restricts to predicates in that namespace."
        ),
    )
    status: StatementStatus | None = StatementStatus.ASSERTED
    as_of: datetime | None = None
    temporal_state: TemporalState | None = None
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _entity_filter_modes(self) -> SearchStatementsRequest:
        end_filters = self.subject_entity_id is not None or self.object_entity_id is not None
        if self.entity_id is not None and end_filters:
            raise ValueError(
                "Use subject_entity_id and/or object_entity_id, or entity_id "
                "(either end), not both modes together"
            )
        return self


class SearchStatementsResponse(BaseModel):
    query: str | None = None
    total: int = 0
    limit: int = 25
    offset: int = 0
    hits: list[RankedStatementHit] = Field(default_factory=list)
    ranking_explanations: list[str] = Field(default_factory=list)


class NeighborhoodEdge(BaseModel):
    statement: StatementResponse
    direction: str
    neighbor_entity_id: uuid.UUID | None = None
    signals: RankingSignals
    ranking_score: float


class NeighborhoodResponse(BaseModel):
    entity_id: uuid.UUID
    edges: list[NeighborhoodEdge] = Field(default_factory=list)
    ranking_explanations: list[str] = Field(default_factory=list)


class MemoryHitType(StrEnum):
    ENTITY = "entity"
    STATEMENT = "statement"
    CONFLICT = "conflict"


class SemanticMemoryHit(BaseModel):
    hit_type: MemoryHitType
    entity: EntityResponse | None = None
    statement: StatementResponse | None = None
    conflict: ConflictResponse | None = None
    signals: RankingSignals
    ranking_score: float
    match_reasons: list[str] = Field(default_factory=list)


class SearchSemanticMemoryRequest(BaseModel):
    query: str = Field(min_length=1)
    entity_id: uuid.UUID | None = None
    class_key: str | None = None
    namespace_key: str = "core"
    as_of: datetime | None = None
    include_conflicts: bool = True
    include_claims: bool = Field(
        default=False,
        description=(
            "When false (default), Claim entities and Claim-binding statements "
            "(makesClaim, claimText, …) are excluded from results. "
            "Set true to opt into epistemic Claim retrieval."
        ),
    )
    limit: int = Field(default=25, ge=1, le=100)


class SearchSemanticMemoryResponse(BaseModel):
    query: str
    hits: list[SemanticMemoryHit] = Field(default_factory=list)
    ranking_explanations: list[str] = Field(default_factory=list)
    vector_search_used: bool = False
    quality_warnings: list[QualityWarning] = Field(default_factory=list)


class RelevantContextRequest(BaseModel):
    query: str | None = None
    entity_id: uuid.UUID | None = None
    statement_id: uuid.UUID | None = None
    namespace_key: str = "core"
    as_of: datetime | None = None
    include_claims: bool = Field(
        default=False,
        description=(
            "When false (default), Claim entities and Claim-binding statements are "
            "excluded for ordinary entity/query context. Direct lookup of a Claim "
            "entity_id always returns Claim structure. Set true to include epistemic "
            "Claims for non-Claim foci."
        ),
    )
    limit: int = Field(default=25, ge=1, le=100)


class RelevantContextResponse(BaseModel):
    entity: EntityResponse | None = None
    timeline: TimelineResponse | None = None
    neighborhood: NeighborhoodResponse | None = None
    statements: list[RankedStatementHit] = Field(default_factory=list)
    conflicts: list[ConflictResponse] = Field(default_factory=list)
    explanation: ExplainStatementResponse | None = None
    ranking_explanations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    quality_warnings: list[QualityWarning] = Field(default_factory=list)


class ObservationSortField(StrEnum):
    OBSERVED_AT = "observed_at"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class QueryObservationsRequest(BaseModel):
    """Paginated typed Observation series for a subject entity.

    ``total`` counts only valid (complete, non-ambiguous) observations after
    filters. Incomplete/ambiguous candidates are excluded from ``observations``
    and counted in ``skipped`` — never silently dropped.
    """

    model_config = ConfigDict(extra="forbid")

    actor_key: str = Field(
        min_length=1,
        description="Caller actor; must hold knowledge.read (same gate as knowledge access).",
    )
    entity_id: uuid.UUID = Field(
        description="Subject Thing whose observations are requested (via observationOf)."
    )
    observation_type: str | None = Field(
        default=None,
        min_length=1,
        description="Optional exact observationType filter (e.g. height, temperature).",
    )
    observed_from: datetime | None = None
    observed_to: datetime | None = None
    order_by: ObservationSortField = ObservationSortField.OBSERVED_AT
    order: SortOrder = SortOrder.ASC
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    include_sources: bool = Field(
        default=False,
        description="When true, attach evidence/sources for the numericValue statement.",
    )
    namespace_key: str = "core"

    @model_validator(mode="after")
    def _date_range(self) -> QueryObservationsRequest:
        if (
            self.observed_from is not None
            and self.observed_to is not None
            and self.observed_from > self.observed_to
        ):
            raise ValueError("observed_from must be <= observed_to")
        return self


class ObservationQuerySkipped(BaseModel):
    """Candidates matching entity (and type filter, when set) that were excluded."""

    missing_observation_type: int = 0
    missing_numeric_value: int = 0
    missing_unit: int = 0
    missing_observed_at: int = 0
    ambiguous_values: int = 0
    not_observation_class: int = 0


class ObservationSourceRef(BaseModel):
    evidence_id: uuid.UUID
    source_id: uuid.UUID
    source_title: str | None = None
    source_uri: str | None = None
    reliability: Decimal | None = None
    excerpt: str | None = None
    locator: str | None = None


class AmbiguousObservation(BaseModel):
    id: uuid.UUID
    reasons: list[str] = Field(default_factory=list)


class ObservationHit(BaseModel):
    id: uuid.UUID
    observation_type: str
    value: Decimal
    unit: str
    observed_at: datetime
    date_precision: str | None = Field(
        default=None,
        description=(
            "Optional precision hint from numericValue metadata (e.g. day). "
            "observed_at is returned as stored; noon UTC does not imply clock time."
        ),
    )
    numeric_value_statement_id: uuid.UUID
    unit_statement_id: uuid.UUID
    observation_type_statement_id: uuid.UUID
    observation_of_statement_id: uuid.UUID
    sources: list[ObservationSourceRef] = Field(default_factory=list)


class QueryObservationsResponse(BaseModel):
    entity_id: uuid.UUID
    observation_type: str | None = None
    total: int = Field(
        description="Count of valid observations matching filters (pagination universe)."
    )
    limit: int
    offset: int
    order_by: ObservationSortField
    order: SortOrder
    skipped: ObservationQuerySkipped
    ambiguous: list[AmbiguousObservation] = Field(default_factory=list)
    observations: list[ObservationHit] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
