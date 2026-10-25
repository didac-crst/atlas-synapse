"""P0 ontology governance reliability: review_failed, clarification recovery, reuse."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from semantic_memory.models import ActorStatus, ActorType, ProposalStatus
from semantic_memory.models.capabilities import DEFAULT_AGENT_CAPABILITIES, Capability
from semantic_memory.models.enums import ProposalType, SemanticClarificationStatus
from semantic_memory.models.governance import OntologySemanticClarificationRequest
from semantic_memory.repositories.actors import ActorRepository
from semantic_memory.repositories.governance import GovernanceRepository
from semantic_memory.schemas.actors import ActorEnsureRequest
from semantic_memory.schemas.proposals import (
    ApplyProposalRequest,
    ProposalOutcome,
    ProposeClassRequest,
)
from semantic_memory.schemas.semantic_review import (
    CLARIFICATION_REASON_CODE,
    REVIEW_OUTCOME_NEEDS_CLARIFICATION,
    REVIEW_OUTCOME_OPEN_PROPOSAL_REUSED,
    REVIEW_OUTCOME_READY_TO_APPLY,
    REVIEW_OUTCOME_REVIEW_FAILED,
    AnswerSemanticClarificationRequest,
    SemanticDecision,
)
from semantic_memory.services.actors import ActorService
from semantic_memory.services.proposals import ProposalService
from semantic_memory.services.review import (
    FailingSemanticReviewer,
    MockSemanticReviewer,
    ReviewDecision,
    make_semantic_review_gate,
    sanitize_reviewer_exception,
)


def _ensure_proposer(session: Session, key: str) -> str:
    ActorService(session).ensure(
        ActorEnsureRequest(
            key=key,
            actor_type=ActorType.AGENT,
            capabilities=[cap.value for cap in DEFAULT_AGENT_CAPABILITIES],
        )
    )
    return key


def _envelope(actor_key: str) -> dict[str, object]:
    return {
        "actor_key": actor_key,
        "request_id": uuid.uuid4(),
        "idempotency_key": f"idem-{uuid.uuid4()}",
    }


def _ambiguous_metadata(**extra: object) -> dict[str, object]:
    meta: dict[str, object] = {
        "review_decision": ReviewDecision.MANUAL_REVIEW.value,
        "review_confidence": 0.94,
        "related_existing_concepts": [
            {"kind": "class", "key": "Skill", "reason": "Potential semantic overlap"}
        ],
        "review_reasons": [
            {
                "code": CLARIFICATION_REASON_CODE,
                "message": "Distinction from Skill is unclear.",
            }
        ],
    }
    meta.update(extra)
    return meta


def test_sanitize_reviewer_exception_redacts_secrets() -> None:
    detail = sanitize_reviewer_exception(
        RuntimeError("openai_unavailable:Authorization Bearer sk-secret")
    )
    assert detail["error_type"] == "RuntimeError"
    assert "sk-secret" not in detail["error_detail"]
    assert detail["failure_category"] in {"network", "runtime_error"}


def test_reviewer_failure_gate_emits_review_failed_reason() -> None:
    gate = make_semantic_review_gate(FailingSemanticReviewer())
    outcome = gate(ProposalType.CLASS, {"namespace_key": "core", "key": "X"})
    assert outcome is not None
    assert outcome.details["reason"] == "reviewer_failure"
    assert outcome.details["outcome_reason"] == REVIEW_OUTCOME_REVIEW_FAILED
    assert "error_detail" in outcome.details
    assert outcome.details["failure_category"]


def test_propose_reviewer_failure_is_distinguishable(db_session: Session) -> None:
    proposer = _ensure_proposer(db_session, "gov-fail")
    service = ProposalService(db_session, reviewer=FailingSemanticReviewer())
    result = service.propose_class(
        ProposeClassRequest(
            **_envelope(proposer),
            key="TransientConcept",
            description="A concept that hits a reviewer outage.",
            parent_keys=["Thing"],
        )
    )
    assert result.outcome == ProposalOutcome.MANUAL_REVIEW
    assert result.outcome_reason == REVIEW_OUTCOME_REVIEW_FAILED
    assert result.proposal.decision_reason == "Semantic reviewer unavailable"
    assert result.open_clarification_request is None


def test_ambiguous_review_uses_needs_clarification_reason(db_session: Session) -> None:
    proposer = _ensure_proposer(db_session, "gov-clarify")
    service = ProposalService(db_session, reviewer=MockSemanticReviewer())
    result = service.propose_class(
        ProposeClassRequest(
            **_envelope(proposer),
            key="CapabilityArea",
            description="Some kind of ability or focus area related to agents.",
            parent_keys=["Thing"],
            metadata=_ambiguous_metadata(),
        )
    )
    assert result.outcome == ProposalOutcome.MANUAL_REVIEW
    assert result.outcome_reason == REVIEW_OUTCOME_NEEDS_CLARIFICATION
    assert result.proposal.decision_reason == "Semantic clarification required"
    assert result.open_clarification_request is not None


def test_clarification_survives_reviewer_failure_and_is_retryable(
    db_session: Session,
) -> None:
    proposer = _ensure_proposer(db_session, "gov-clar-retry")
    mock = MockSemanticReviewer()
    service = ProposalService(db_session, reviewer=mock)
    proposed = service.propose_class(
        ProposeClassRequest(
            **_envelope(proposer),
            key="CapabilityArea",
            description="Some kind of ability or focus area related to agents.",
            parent_keys=["Thing"],
            metadata=_ambiguous_metadata(
                challenge_decision=ReviewDecision.APPROVE.value,
            ),
        )
    )
    clar = proposed.open_clarification_request
    assert clar is not None

    # Swap in a failing reviewer for the clarification re-evaluation.
    service_fail = ProposalService(db_session, reviewer=FailingSemanticReviewer())
    failed = service_fail.answer_semantic_clarification(
        AnswerSemanticClarificationRequest(
            **_envelope(proposer),
            clarification_request_id=clar.clarification_request_id,
            response=(
                "CapabilityArea is a domain grouping such as Data Engineering. "
                "Skill is a concrete competence such as SQL optimization."
            ),
        )
    )
    assert failed.outcome_reason == REVIEW_OUTCOME_REVIEW_FAILED
    assert failed.clarification_status == SemanticClarificationStatus.OPEN
    assert failed.resolved_by_review_id is None
    assert failed.open_clarification_request is not None
    assert (
        failed.open_clarification_request.clarification_request_id
        == clar.clarification_request_id
    )

    row = db_session.get(OntologySemanticClarificationRequest, clar.clarification_request_id)
    assert row is not None
    assert row.status == SemanticClarificationStatus.OPEN.value
    assert row.answer_text is not None
    assert "CapabilityArea" in row.answer_text

    # Retry against the same clarification after reviewer recovery.
    recovered = service.answer_semantic_clarification(
        AnswerSemanticClarificationRequest(
            **_envelope(proposer),
            clarification_request_id=clar.clarification_request_id,
            response=(
                "CapabilityArea is a domain grouping such as Data Engineering. "
                "Skill is a concrete competence such as SQL optimization. "
                "A person may have multiple Skills under one CapabilityArea."
            ),
        )
    )
    assert recovered.outcome_reason == REVIEW_OUTCOME_READY_TO_APPLY
    assert recovered.clarification_status == SemanticClarificationStatus.RESOLVED
    assert recovered.review.decision == SemanticDecision.APPROVE


def test_repropose_reuses_open_proposal(db_session: Session) -> None:
    proposer = _ensure_proposer(db_session, "gov-reuse")
    service = ProposalService(db_session, reviewer=FailingSemanticReviewer())
    first = service.propose_class(
        ProposeClassRequest(
            **_envelope(proposer),
            key="MedicalEvent",
            description="Clinically significant health occurrence.",
            parent_keys=["Event"],
        )
    )
    assert first.outcome_reason == REVIEW_OUTCOME_REVIEW_FAILED
    second = service.propose_class(
        ProposeClassRequest(
            **_envelope(proposer),
            key="MedicalEvent",
            description="Clinically significant health occurrence (retry).",
            parent_keys=["Event"],
        )
    )
    assert second.outcome_reason == REVIEW_OUTCOME_OPEN_PROPOSAL_REUSED
    assert second.proposal.id == first.proposal.id


def test_accepted_proposal_cancels_open_siblings(db_session: Session) -> None:
    proposer = _ensure_proposer(db_session, "gov-sibling")
    fail_service = ProposalService(db_session, reviewer=FailingSemanticReviewer())
    stuck = fail_service.propose_class(
        ProposeClassRequest(
            **_envelope(proposer),
            key="SiblingEvent",
            description="First attempt that hits reviewer failure.",
            parent_keys=["Event"],
        )
    )
    assert stuck.proposal.status == ProposalStatus.IN_REVIEW

    gov = GovernanceRepository(db_session)
    stuck_row = gov.get_proposal(stuck.proposal.id)
    assert stuck_row is not None
    # Park the stuck proposal so we can create a second open one, then restore.
    gov.set_proposal_status(stuck_row, status=ProposalStatus.CANCELLED, decision_reason="park")
    ok_service = ProposalService(db_session, reviewer=MockSemanticReviewer())
    ready = ok_service.propose_class(
        ProposeClassRequest(
            **_envelope(proposer),
            key="SiblingEvent",
            description="Second attempt that the reviewer approves.",
            parent_keys=["Event"],
            metadata={"review_decision": ReviewDecision.APPROVE.value},
        )
    )
    assert ready.outcome == ProposalOutcome.READY_TO_APPLY
    gov.set_proposal_status(
        stuck_row,
        status=ProposalStatus.IN_REVIEW,
        decision_reason="Semantic reviewer unavailable",
    )

    applier = "gov-sibling-apply"
    ActorRepository(db_session).create(
        key=applier,
        actor_type=ActorType.SERVICE,
        status=ActorStatus.ACTIVE,
        capabilities=[
            Capability.ONTOLOGY_READ.value,
            Capability.ONTOLOGY_PROPOSE.value,
            Capability.ONTOLOGY_APPLY.value,
        ],
    )
    applied = ok_service.apply_proposal(
        ApplyProposalRequest(
            **_envelope(applier),
            proposal_id=ready.proposal.id,
        )
    )
    assert applied.outcome == ProposalOutcome.APPLIED
    db_session.refresh(stuck_row)
    assert stuck_row.status == ProposalStatus.CANCELLED.value
    assert "Superseded by accepted proposal" in (stuck_row.decision_reason or "")
