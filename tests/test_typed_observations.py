"""Governed typed Observation model: propose/apply predicates + numeric queries."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from semantic_memory.models import ActorStatus, ActorType
from semantic_memory.models.capabilities import Capability
from semantic_memory.models.enums import BatchStatus, Cardinality, ValueKind
from semantic_memory.ontology.observation_predicates import (
    OBSERVATION_PREDICATE_PROPOSALS,
    observation_predicate_keys,
)
from semantic_memory.repositories.actors import ActorRepository
from semantic_memory.schemas.actors import ActorEnsureRequest
from semantic_memory.schemas.batches import AssertBatchRequest, BatchEntityItem, BatchStatementItem
from semantic_memory.schemas.entities import CreateEntityRequest
from semantic_memory.schemas.proposals import (
    ApplyProposalRequest,
    ProposalOutcome,
    ProposePredicateRequest,
)
from semantic_memory.schemas.retrieval import SearchStatementsRequest
from semantic_memory.schemas.statements import AssertStatementRequest
from semantic_memory.services.actors import ActorService
from semantic_memory.services.batches import BatchService
from semantic_memory.services.entities import EntityService
from semantic_memory.services.proposals import ProposalService
from semantic_memory.services.retrieval import RetrievalService
from semantic_memory.services.review import MockSemanticReviewer, ReviewDecision
from semantic_memory.services.statements import StatementService


def _ensure_writer(session: Session) -> str:
    key = "obs-writer"
    ActorService(session).ensure(ActorEnsureRequest(key=key, actor_type=ActorType.AGENT))
    return key


def _ensure_applier(session: Session) -> str:
    key = "obs-applier"
    ActorRepository(session).create(
        key=key,
        actor_type=ActorType.SERVICE,
        status=ActorStatus.ACTIVE,
        capabilities=[
            Capability.ONTOLOGY_READ.value,
            Capability.ONTOLOGY_PROPOSE.value,
            Capability.ONTOLOGY_APPLY.value,
        ],
    )
    return key


def _envelope(actor_key: str) -> dict[str, object]:
    return {
        "actor_key": actor_key,
        "request_id": uuid.uuid4(),
        "idempotency_key": f"idem-{uuid.uuid4()}",
    }


def _install_observation_predicates(session: Session) -> None:
    proposer = _ensure_writer(session)
    applier = _ensure_applier(session)
    proposals = ProposalService(session, reviewer=MockSemanticReviewer())
    for spec in OBSERVATION_PREDICATE_PROPOSALS:
        proposed = proposals.propose_predicate(
            ProposePredicateRequest(
                **_envelope(proposer),
                key=str(spec["key"]),
                label=str(spec["label"]),
                description=str(spec["description"]),
                value_kind=ValueKind(spec["value_kind"]),
                cardinality=Cardinality(spec["cardinality"]),
                domain_keys=list(spec["domain_keys"]),
                range_keys=list(spec["range_keys"]),
                is_symmetric=bool(spec["is_symmetric"]),
                is_transitive=bool(spec["is_transitive"]),
                summary=str(spec["summary"]),
                metadata={"review_decision": ReviewDecision.APPROVE.value},
            )
        )
        assert proposed.outcome == ProposalOutcome.READY_TO_APPLY, proposed.outcome
        applied = proposals.apply_proposal(
            ApplyProposalRequest(**_envelope(applier), proposal_id=proposed.proposal.id)
        )
        assert applied.outcome == ProposalOutcome.APPLIED


def _create(session: Session, *, name: str, class_key: str, actor: str) -> uuid.UUID:
    result = EntityService(session).create_entity(
        CreateEntityRequest(
            **_envelope(actor),
            canonical_name=name,
            class_key=class_key,
        )
    )
    assert result.entity is not None
    return result.entity.id


def _assert(session: Session, actor: str, **kwargs: object) -> uuid.UUID:
    result = StatementService(session).assert_statement(
        AssertStatementRequest(**_envelope(actor), **kwargs)
    )
    return result.statement.id


def test_observation_predicate_catalog_is_generic() -> None:
    keys = observation_predicate_keys()
    assert keys == ("observationOf", "observationType", "numericValue", "unit")
    assert all("medical" not in k.lower() for k in keys)
    assert all("height" not in k.lower() for k in keys)


def test_typed_observations_support_person_and_device_numeric_queries(
    db_session: Session,
) -> None:
    actor = _ensure_writer(db_session)
    _install_observation_predicates(db_session)

    person = _create(db_session, name="Siena-test", class_key="Person", actor=actor)
    device = _create(db_session, name="Thermostat-lab", class_key="Thing", actor=actor)

    h1 = _create(db_session, name="Siena height 2026-02-13", class_key="Observation", actor=actor)
    h2 = _create(db_session, name="Siena height 2026-10-25", class_key="Observation", actor=actor)
    t1 = _create(db_session, name="Thermostat reading", class_key="Observation", actor=actor)

    measured_early = datetime(2026, 2, 13, 12, 0, tzinfo=UTC)
    measured_late = datetime(2026, 10, 25, 12, 0, tzinfo=UTC)
    measured_temp = datetime(2026, 10, 25, 8, 0, tzinfo=UTC)

    for obs, subject, obs_type, value, unit, when in (
        (h1, person, "height", Decimal("102"), "cm", measured_early),
        (h2, person, "height", Decimal("106"), "cm", measured_late),
        (t1, device, "temperature", Decimal("21.5"), "C", measured_temp),
    ):
        _assert(
            db_session,
            actor,
            subject_entity_id=obs,
            predicate_key="observationOf",
            object_entity_id=subject,
        )
        _assert(
            db_session,
            actor,
            subject_entity_id=obs,
            predicate_key="observationType",
            object_string=obs_type,
        )
        _assert(
            db_session,
            actor,
            subject_entity_id=obs,
            predicate_key="numericValue",
            object_number=value,
            observed_at=when,
        )
        _assert(
            db_session,
            actor,
            subject_entity_id=obs,
            predicate_key="unit",
            object_string=unit,
        )

    # Second height must not supersede the first (separate Observation entities).
    retrieval = RetrievalService(db_session)
    numbers: list[Decimal] = []
    for obs_id in (h1, h2):
        values = retrieval.search_statements(
            SearchStatementsRequest(
                predicate_key="numericValue",
                subject_entity_id=obs_id,
                limit=10,
            )
        )
        assert len(values.hits) == 1
        assert values.hits[0].statement.object_number is not None
        numbers.append(Decimal(str(values.hits[0].statement.object_number)))
    numbers = sorted(numbers)
    assert numbers == [Decimal("102"), Decimal("106")]
    assert (numbers[1] - numbers[0]) == Decimal("4")

    # Device temperature uses the same predicates (generic Thing range).
    device_vals = retrieval.search_statements(
        SearchStatementsRequest(
            predicate_key="numericValue",
            subject_entity_id=t1,
            limit=5,
        )
    )
    assert len(device_vals.hits) == 1
    assert Decimal(str(device_vals.hits[0].statement.object_number)) == Decimal("21.5")

    of_person = retrieval.search_statements(
        SearchStatementsRequest(
            predicate_key="observationOf",
            object_entity_id=person,
            limit=10,
        )
    )
    assert {hit.statement.subject_entity_id for hit in of_person.hits} == {h1, h2}


def test_assert_batch_creates_observation_atomically(db_session: Session) -> None:
    actor = _ensure_writer(db_session)
    _install_observation_predicates(db_session)
    person = _create(db_session, name="Batch-Person", class_key="Person", actor=actor)
    when = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)

    result = BatchService(db_session).assert_batch(
        AssertBatchRequest(
            **_envelope(actor),
            entities=[
                BatchEntityItem(
                    client_item_id="obs-1",
                    canonical_name="Batch-Person height 2026-03-01",
                    class_key="Observation",
                )
            ],
            statements=[
                BatchStatementItem(
                    client_item_id="of-1",
                    subject_client_item_id="obs-1",
                    predicate_key="observationOf",
                    object_entity_id=person,
                ),
                BatchStatementItem(
                    client_item_id="type-1",
                    subject_client_item_id="obs-1",
                    predicate_key="observationType",
                    object_string="height",
                ),
                BatchStatementItem(
                    client_item_id="val-1",
                    subject_client_item_id="obs-1",
                    predicate_key="numericValue",
                    object_number=Decimal("100"),
                    observed_at=when,
                ),
                BatchStatementItem(
                    client_item_id="unit-1",
                    subject_client_item_id="obs-1",
                    predicate_key="unit",
                    object_string="cm",
                ),
            ],
        )
    )
    assert result.status == BatchStatus.SUCCEEDED
    assert result.rejected == []
    assert result.ambiguous == []
    assert result.ontology_required == []
    created_obs = next(item for item in result.created if item.entity is not None)
    assert created_obs.entity is not None and created_obs.entity.entity is not None
    obs_id = created_obs.entity.entity.id

    values = RetrievalService(db_session).search_statements(
        SearchStatementsRequest(predicate_key="numericValue", subject_entity_id=obs_id)
    )
    assert len(values.hits) == 1
    assert Decimal(str(values.hits[0].statement.object_number)) == Decimal("100")
    assert values.hits[0].statement.observed_at == when
