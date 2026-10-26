"""query_observations: paginated typed Observation series retrieval."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from semantic_memory.exceptions import UnauthorizedOperationError, UnknownEntityError
from semantic_memory.models import ActorStatus, ActorType
from semantic_memory.models.capabilities import Capability
from semantic_memory.repositories.actors import ActorRepository
from semantic_memory.schemas.actors import ActorEnsureRequest
from semantic_memory.schemas.provenance import AddEvidenceRequest, EnsureSourceRequest
from semantic_memory.schemas.retrieval import QueryObservationsRequest, SortOrder
from semantic_memory.schemas.statements import AssertStatementRequest
from semantic_memory.services.actors import ActorService
from semantic_memory.services.provenance import ProvenanceService
from semantic_memory.services.retrieval import RetrievalService
from semantic_memory.services.statements import StatementService
from test_typed_observations import (
    _assert,
    _create,
    _ensure_writer,
    _envelope,
    _install_observation_predicates,
)


def _create_observation(
    session: Session,
    *,
    actor: str,
    person_id: uuid.UUID,
    name: str,
    obs_type: str,
    value: Decimal,
    unit: str,
    observed_at: datetime,
    date_precision: str | None = None,
) -> uuid.UUID:
    obs = _create(session, name=name, class_key="Observation", actor=actor)
    _assert(
        session,
        actor,
        subject_entity_id=obs,
        predicate_key="observationOf",
        object_entity_id=person_id,
    )
    _assert(
        session,
        actor,
        subject_entity_id=obs,
        predicate_key="observationType",
        object_string=obs_type,
    )
    kwargs: dict[str, object] = {
        **_envelope(actor),
        "subject_entity_id": obs,
        "predicate_key": "numericValue",
        "object_number": value,
        "observed_at": observed_at,
    }
    if date_precision is not None:
        kwargs["metadata"] = {"date_precision": date_precision}
    StatementService(session).assert_statement(AssertStatementRequest(**kwargs))
    _assert(
        session,
        actor,
        subject_entity_id=obs,
        predicate_key="unit",
        object_string=unit,
    )
    return obs


def _seed_height_series(
    session: Session,
    *,
    actor: str,
    person_name: str,
    start: datetime,
    count: int,
    base_cm: int,
) -> uuid.UUID:
    person = _create(session, name=person_name, class_key="Person", actor=actor)
    for i in range(count):
        when = start + timedelta(days=30 * i)
        _create_observation(
            session,
            actor=actor,
            person_id=person,
            name=f"{person_name} — height — {when.date().isoformat()}",
            obs_type="height",
            value=Decimal(base_cm + i),
            unit="cm",
            observed_at=when,
            date_precision="day",
        )
    return person


def test_query_observations_siena_and_elma_heights(db_session: Session) -> None:
    actor = _ensure_writer(db_session)
    _install_observation_predicates(db_session)
    start = datetime(2021, 6, 13, 12, 0, tzinfo=UTC)
    siena = _seed_height_series(
        db_session, actor=actor, person_name="QO-Siena", start=start, count=15, base_cm=56
    )
    elma = _seed_height_series(
        db_session, actor=actor, person_name="QO-Elma", start=start, count=15, base_cm=59
    )

    retrieval = RetrievalService(db_session)
    siena_page = retrieval.query_observations(
        QueryObservationsRequest(
            actor_key=actor,
            entity_id=siena,
            observation_type="height",
            order=SortOrder.ASC,
            limit=50,
        )
    )
    elma_page = retrieval.query_observations(
        QueryObservationsRequest(
            actor_key=actor,
            entity_id=elma,
            observation_type="height",
            order=SortOrder.ASC,
            limit=50,
        )
    )

    assert siena_page.total == 15
    assert len(siena_page.observations) == 15
    assert [hit.value for hit in siena_page.observations] == [Decimal(56 + i) for i in range(15)]
    assert all(hit.unit == "cm" for hit in siena_page.observations)
    assert all(hit.observation_type == "height" for hit in siena_page.observations)
    assert all(hit.date_precision == "day" for hit in siena_page.observations)
    # Placeholder noon preserved; do not rewrite.
    assert siena_page.observations[0].observed_at == start
    assert siena_page.skipped.model_dump() == {
        "missing_observation_type": 0,
        "missing_numeric_value": 0,
        "missing_unit": 0,
        "missing_observed_at": 0,
        "ambiguous_values": 0,
        "not_observation_class": 0,
    }

    assert elma_page.total == 15
    assert [hit.value for hit in elma_page.observations] == [Decimal(59 + i) for i in range(15)]
    observed = [hit.observed_at for hit in siena_page.observations]
    assert observed == sorted(observed)


def test_query_observations_non_medical_device_temperature(db_session: Session) -> None:
    actor = _ensure_writer(db_session)
    _install_observation_predicates(db_session)
    device = _create(db_session, name="QO-Server-Rack", class_key="Thing", actor=actor)
    when = datetime(2026, 4, 1, 9, 30, tzinfo=UTC)
    _create_observation(
        db_session,
        actor=actor,
        person_id=device,
        name="QO-Server-Rack — temperature — 2026-04-01",
        obs_type="temperature",
        value=Decimal("21.5"),
        unit="C",
        observed_at=when,
    )
    result = RetrievalService(db_session).query_observations(
        QueryObservationsRequest(
            actor_key=actor,
            entity_id=device,
            observation_type="temperature",
        )
    )
    assert result.total == 1
    assert result.observations[0].value == Decimal("21.5")
    assert result.observations[0].unit == "C"
    assert result.observations[0].observed_at == when


def test_query_observations_pagination_and_date_filter(db_session: Session) -> None:
    actor = _ensure_writer(db_session)
    _install_observation_predicates(db_session)
    start = datetime(2024, 1, 1, 12, 0, tzinfo=UTC)
    person = _seed_height_series(
        db_session, actor=actor, person_name="QO-Page", start=start, count=10, base_cm=100
    )
    retrieval = RetrievalService(db_session)

    page0 = retrieval.query_observations(
        QueryObservationsRequest(
            actor_key=actor,
            entity_id=person,
            observation_type="height",
            limit=3,
            offset=0,
        )
    )
    page1 = retrieval.query_observations(
        QueryObservationsRequest(
            actor_key=actor,
            entity_id=person,
            observation_type="height",
            limit=3,
            offset=3,
        )
    )
    assert page0.total == 10
    assert [hit.value for hit in page0.observations] == [
        Decimal("100"),
        Decimal("101"),
        Decimal("102"),
    ]
    assert [hit.value for hit in page1.observations] == [
        Decimal("103"),
        Decimal("104"),
        Decimal("105"),
    ]

    filtered = retrieval.query_observations(
        QueryObservationsRequest(
            actor_key=actor,
            entity_id=person,
            observation_type="height",
            observed_from=start + timedelta(days=30 * 2),
            observed_to=start + timedelta(days=30 * 4),
        )
    )
    assert filtered.total == 3
    assert [hit.value for hit in filtered.observations] == [
        Decimal("102"),
        Decimal("103"),
        Decimal("104"),
    ]


def test_query_observations_incomplete_and_ambiguous(db_session: Session) -> None:
    actor = _ensure_writer(db_session)
    _install_observation_predicates(db_session)
    person = _create(db_session, name="QO-Incomplete", class_key="Person", actor=actor)
    when = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)

    # Missing unit.
    missing_unit = _create(
        db_session, name="QO-Incomplete missing unit", class_key="Observation", actor=actor
    )
    _assert(
        db_session,
        actor,
        subject_entity_id=missing_unit,
        predicate_key="observationOf",
        object_entity_id=person,
    )
    _assert(
        db_session,
        actor,
        subject_entity_id=missing_unit,
        predicate_key="observationType",
        object_string="height",
    )
    _assert(
        db_session,
        actor,
        subject_entity_id=missing_unit,
        predicate_key="numericValue",
        object_number=Decimal("110"),
        observed_at=when,
    )

    # Missing observed_at.
    missing_time = _create(
        db_session, name="QO-Incomplete missing time", class_key="Observation", actor=actor
    )
    _assert(
        db_session,
        actor,
        subject_entity_id=missing_time,
        predicate_key="observationOf",
        object_entity_id=person,
    )
    _assert(
        db_session,
        actor,
        subject_entity_id=missing_time,
        predicate_key="observationType",
        object_string="height",
    )
    _assert(
        db_session,
        actor,
        subject_entity_id=missing_time,
        predicate_key="numericValue",
        object_number=Decimal("111"),
    )
    _assert(
        db_session,
        actor,
        subject_entity_id=missing_time,
        predicate_key="unit",
        object_string="cm",
    )

    # Ambiguous numericValue: second asserted value without superseding the first.
    ambiguous = _create_observation(
        db_session,
        actor=actor,
        person_id=person,
        name="QO-Incomplete ambiguous",
        obs_type="height",
        value=Decimal("112"),
        unit="cm",
        observed_at=when,
    )
    # Force a second asserted numericValue (bypass cardinality by direct insert path:
    # assert_statement would conflict-record but still create if cardinality allows
    # overlapping — for ONE it records conflict but both stay asserted).
    StatementService(db_session).assert_statement(
        AssertStatementRequest(
            **_envelope(actor),
            subject_entity_id=ambiguous,
            predicate_key="numericValue",
            object_number=Decimal("113"),
            observed_at=when,
        )
    )

    # One valid row for contrast.
    _create_observation(
        db_session,
        actor=actor,
        person_id=person,
        name="QO-Incomplete valid",
        obs_type="height",
        value=Decimal("114"),
        unit="cm",
        observed_at=when + timedelta(days=1),
    )

    result = RetrievalService(db_session).query_observations(
        QueryObservationsRequest(
            actor_key=actor,
            entity_id=person,
            observation_type="height",
        )
    )
    assert result.total == 1
    assert result.observations[0].value == Decimal("114")
    assert result.skipped.missing_unit == 1
    assert result.skipped.missing_observed_at == 1
    assert result.skipped.ambiguous_values == 1
    assert len(result.ambiguous) == 1
    assert result.ambiguous[0].id == ambiguous
    assert "ambiguous_numericValue" in result.ambiguous[0].reasons

    # Ambiguous observation must not multiply into the valid series.
    assert result.total == 1


def test_query_observations_authorization(db_session: Session) -> None:
    writer = _ensure_writer(db_session)
    _install_observation_predicates(db_session)
    person = _create(db_session, name="QO-Auth", class_key="Person", actor=writer)
    _create_observation(
        db_session,
        actor=writer,
        person_id=person,
        name="QO-Auth height",
        obs_type="height",
        value=Decimal("100"),
        unit="cm",
        observed_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
    )

    ActorRepository(db_session).create(
        key="qo-readonly-denied",
        actor_type=ActorType.AGENT,
        status=ActorStatus.ACTIVE,
        capabilities=[Capability.FEEDBACK_CREATE.value],  # no knowledge.read
    )
    with pytest.raises(UnauthorizedOperationError):
        RetrievalService(db_session).query_observations(
            QueryObservationsRequest(
                actor_key="qo-readonly-denied",
                entity_id=person,
                observation_type="height",
            )
        )

    with pytest.raises(UnknownEntityError):
        RetrievalService(db_session).query_observations(
            QueryObservationsRequest(
                actor_key=writer,
                entity_id=uuid.uuid4(),
            )
        )


def test_query_observations_include_sources(db_session: Session) -> None:
    actor = _ensure_writer(db_session)
    _install_observation_predicates(db_session)
    person = _create(db_session, name="QO-Source", class_key="Person", actor=actor)
    when = datetime(2026, 2, 13, 12, 0, tzinfo=UTC)
    obs = _create_observation(
        db_session,
        actor=actor,
        person_id=person,
        name="QO-Source height",
        obs_type="height",
        value=Decimal("102"),
        unit="cm",
        observed_at=when,
        date_precision="day",
    )
    values = RetrievalService(db_session).query_observations(
        QueryObservationsRequest(actor_key=actor, entity_id=person, observation_type="height")
    )
    numeric_id = values.observations[0].numeric_value_statement_id

    ProvenanceService(db_session).ensure_source(
        EnsureSourceRequest(
            **_envelope(actor),
            source_system="growth-app",
            external_id="qo-shot-1",
            title="Growth screenshot",
            uri="https://example.test/shot.png",
            reliability=Decimal("0.8"),
        )
    )
    ProvenanceService(db_session).add_evidence(
        AddEvidenceRequest(
            **_envelope(actor),
            statement_id=numeric_id,
            source={
                "source_system": "growth-app",
                "external_id": "qo-shot-1",
            },
            excerpt="102 cm",
            locator="screenshot",
        )
    )

    with_sources = RetrievalService(db_session).query_observations(
        QueryObservationsRequest(
            actor_key=actor,
            entity_id=person,
            observation_type="height",
            include_sources=True,
        )
    )
    assert len(with_sources.observations[0].sources) == 1
    assert with_sources.observations[0].sources[0].source_title == "Growth screenshot"
    assert with_sources.observations[0].date_precision == "day"
    assert obs == with_sources.observations[0].id


def test_mcp_query_observations_e2e(db_session: Session) -> None:
    from semantic_memory.config import get_settings
    from semantic_memory.mcp.tools import RetrievalMCPTools

    actor = _ensure_writer(db_session)
    _install_observation_predicates(db_session)
    start = datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    siena = _seed_height_series(
        db_session, actor=actor, person_name="QO-MCP-Siena", start=start, count=15, base_cm=90
    )
    # MCP injects configured actor — ensure it exists with knowledge.read.
    settings = get_settings()
    ActorService(db_session).ensure(
        ActorEnsureRequest(key=settings.mcp_actor_key, actor_type=ActorType.AGENT)
    )

    payload = RetrievalMCPTools(db_session).query_observations(
        {
            "entity_id": str(siena),
            "observation_type": "height",
            "order": "asc",
            "limit": 50,
        }
    )
    assert "error_code" not in payload
    assert payload["total"] == 15
    assert len(payload["observations"]) == 15
    assert payload["observations"][0]["value"] == "90"
    assert payload["observations"][-1]["value"] == "104"
    assert payload["observations"][0]["date_precision"] == "day"
