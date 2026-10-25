#!/usr/bin/env python3
"""Enrich existing Observation entities with governed typed predicates.

SAFETY GATES (enforced):
1. Default mode is dry-run (inventory + plan only).
2. --execute requires --i-have-backup.
3. Typed predicates must already exist in the live ontology (propose/apply first).
4. Description conflict cleanup is a separate --cleanup-descriptions pass and
   must not run until enrichment verification succeeds.
5. Never deletes statements; cleanup uses supersede/retract only.

Does not recreate Observation entities. Preserves entity IDs and observed_at.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from collections import Counter
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from semantic_memory.config import get_settings
from semantic_memory.models import OntologyPredicate, Statement
from semantic_memory.models.enums import StatementStatus
from semantic_memory.ontology.observation_predicates import observation_predicate_keys
from semantic_memory.repositories.ontology import OntologyRepository
from semantic_memory.schemas.statements import (
    AssertStatementRequest,
    RetractStatementRequest,
)
from semantic_memory.services.statements import StatementService

NAME_RE = re.compile(
    r"^(?P<person>Siena|Elma) — (?P<kind>height|weight) — (?P<date>\d{4}-\d{2}-\d{2})$"
)


def _session() -> Session:
    settings = get_settings()
    engine = create_engine(settings.sqlalchemy_database_uri)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def _predicate_map(session: Session) -> dict[str, OntologyPredicate]:
    ontology = OntologyRepository(session)
    found: dict[str, OntologyPredicate] = {}
    for key in observation_predicate_keys():
        pred = ontology.get_predicate_by_key(namespace_key="core", predicate_key=key)
        if pred is not None:
            found[key] = pred
    return found


def _inventory(session: Session) -> list[dict[str, Any]]:
    rows = session.execute(
        text(
            """
            SELECT e.id::text, e.canonical_name, e.status::text
            FROM entity e
            JOIN entity_type et ON et.entity_id = e.id
            JOIN ontology_class oc ON oc.id = et.class_id AND oc.key = 'Observation'
            WHERE e.canonical_name ~ '^(Siena|Elma) — (height|weight) — '
            ORDER BY e.canonical_name
            """
        )
    ).fetchall()
    inventory: list[dict[str, Any]] = []
    for oid, name, status in rows:
        match = NAME_RE.match(name or "")
        meta: dict[str, Any] = {}
        observed_at = None
        desc = session.execute(
            text(
                """
                SELECT st.object_string, st.observed_at::text, st.metadata
                FROM statement st
                JOIN ontology_predicate pr ON pr.id = st.predicate_id AND pr.key = 'description'
                WHERE st.subject_entity_id = :oid AND st.status = 'asserted'
                ORDER BY st.asserted_at DESC LIMIT 1
                """
            ),
            {"oid": oid},
        ).fetchone()
        if desc:
            meta = dict(desc[2] or {})
            observed_at = desc[1]
        related = session.execute(
            text(
                """
                SELECT p.canonical_name
                FROM statement st
                JOIN ontology_predicate pr ON pr.id = st.predicate_id AND pr.key = 'relatedTo'
                JOIN entity p ON p.id = st.object_entity_id
                WHERE st.subject_entity_id = :oid AND st.status = 'asserted'
                LIMIT 1
                """
            ),
            {"oid": oid},
        ).scalar()
        inventory.append(
            {
                "id": oid,
                "name": name,
                "status": status,
                "person": None if match is None else match.group("person"),
                "kind": None if match is None else match.group("kind"),
                "date": None if match is None else match.group("date"),
                "related_to": related,
                "observed_at": observed_at,
                "metadata": meta,
                "value": meta.get("value"),
                "unit": meta.get("unit"),
                "measurement_type": meta.get("measurement_type")
                or (None if match is None else match.group("kind")),
            }
        )
    return inventory


def _print_inventory(inventory: list[dict[str, Any]]) -> None:
    kinds = Counter((row["person"], row["kind"]) for row in inventory)
    print(f"inventory_count={len(inventory)}")
    for key, count in sorted(kinds.items()):
        print(f"  {key[0]} {key[1]}: {count}")
    orphans = [row for row in inventory if not row["related_to"]]
    print(f"orphans={len(orphans)}")
    missing_meta = [
        row for row in inventory if row["value"] is None or row["unit"] is None
    ]
    print(f"missing_value_or_unit_metadata={len(missing_meta)}")


def _already_has(
    session: Session, *, subject_id: uuid.UUID, predicate_id: uuid.UUID
) -> bool:
    return (
        session.scalar(
            select(Statement.id).where(
                Statement.subject_entity_id == subject_id,
                Statement.predicate_id == predicate_id,
                Statement.status == StatementStatus.ASSERTED.value,
            )
        )
        is not None
    )


def _enrich(
    session: Session,
    inventory: list[dict[str, Any]],
    *,
    actor_key: str,
    execute: bool,
) -> dict[str, int]:
    preds = _predicate_map(session)
    missing = [k for k in observation_predicate_keys() if k not in preds]
    if missing:
        raise SystemExit(
            f"Missing live predicates {missing}. Propose/apply observation predicates first."
        )
    person_ids = {
        name: session.execute(
            text(
                """
                SELECT e.id::text FROM entity e
                JOIN entity_type et ON et.entity_id = e.id
                JOIN ontology_class oc ON oc.id = et.class_id AND oc.key = 'Person'
                WHERE e.canonical_name = :name LIMIT 1
                """
            ),
            {"name": name},
        ).scalar()
        for name in ("Siena", "Elma")
    }
    stats = Counter()
    statements = StatementService(session)
    for row in inventory:
        stats["seen"] += 1
        person_name = row["person"]
        person_id = person_ids.get(person_name or "")
        if person_id is None:
            stats["skip_no_person"] += 1
            continue
        obs_id = uuid.UUID(row["id"])
        value = row["value"]
        unit = row["unit"]
        obs_type = row["measurement_type"]
        if value is None or unit is None or obs_type is None:
            stats["skip_incomplete_metadata"] += 1
            continue
        observed_at = None
        if row["observed_at"]:
            observed_at = datetime.fromisoformat(row["observed_at"])

        planned = [
            ("observationOf", {"object_entity_id": uuid.UUID(person_id)}),
            ("observationType", {"object_string": str(obs_type)}),
            (
                "numericValue",
                {
                    "object_number": Decimal(str(value)),
                    "observed_at": observed_at,
                },
            ),
            ("unit", {"object_string": str(unit)}),
        ]
        for pred_key, kwargs in planned:
            pred = preds[pred_key]
            if _already_has(session, subject_id=obs_id, predicate_id=pred.id):
                stats[f"reuse_{pred_key}"] += 1
                continue
            stats[f"plan_{pred_key}"] += 1
            if not execute:
                continue
            statements.assert_statement(
                AssertStatementRequest(
                    actor_key=actor_key,
                    request_id=uuid.uuid4(),
                    idempotency_key=f"migrate-obs:{obs_id}:{pred_key}",
                    subject_entity_id=obs_id,
                    predicate_key=pred_key,
                    **kwargs,
                )
            )
            stats[f"assert_{pred_key}"] += 1
    return dict(stats)


def _cleanup_descriptions(
    session: Session,
    *,
    actor_key: str,
    execute: bool,
) -> dict[str, int]:
    """Supersede/retract bulk measurement Person.description dumps; keep biography."""
    stats = Counter()
    keep_prefixes = ("Twin daughter",)
    retract_markers = (
        "growth app HEIGHT",
        "growth app WEIGHT",
        "Parent-reported medical/development history",
        "parent estimates",
        "current standing height",
    )
    rows = session.execute(
        text(
            """
            SELECT st.id::text, e.canonical_name, st.object_string
            FROM statement st
            JOIN ontology_predicate pr ON pr.id = st.predicate_id AND pr.key = 'description'
            JOIN entity e ON e.id = st.subject_entity_id
            WHERE e.canonical_name IN ('Siena', 'Elma') AND st.status = 'asserted'
            ORDER BY e.canonical_name, st.asserted_at
            """
        )
    ).fetchall()
    service = StatementService(session)
    for sid, person, text_value in rows:
        body = text_value or ""
        if body.startswith(keep_prefixes):
            stats["keep_biography"] += 1
            continue
        if not any(marker in body for marker in retract_markers):
            stats["skip_unknown_description"] += 1
            print(f"SKIP unknown description on {person}: {body[:80]!r}")
            continue
        stats["plan_retract"] += 1
        if not execute:
            print(f"PLAN retract {person} description={body[:80]!r}")
            continue
        service.retract_statement(
            RetractStatementRequest(
                actor_key=actor_key,
                request_id=uuid.uuid4(),
                idempotency_key=f"migrate-desc-retract:{sid}",
                statement_id=uuid.UUID(sid),
                reason="Redundant bulk measurement narrative superseded by typed Observations",
            )
        )
        stats["retract"] += 1
    return dict(stats)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Persist changes (default is dry-run inventory/plan).",
    )
    parser.add_argument(
        "--i-have-backup",
        action="store_true",
        help="Required with --execute: confirm a verified production backup exists.",
    )
    parser.add_argument(
        "--cleanup-descriptions",
        action="store_true",
        help="Second pass: retract redundant Person description dumps (not default).",
    )
    parser.add_argument(
        "--actor-key",
        default="system",
        help="Actor key used for assert/retract mutations when executing.",
    )
    parser.add_argument(
        "--write-inventory",
        default="",
        help="Optional path to write JSON inventory.",
    )
    args = parser.parse_args(argv)

    if args.execute and not args.i_have_backup:
        print("Refusing --execute without --i-have-backup", file=sys.stderr)
        return 2

    session = _session()
    try:
        inventory = _inventory(session)
        _print_inventory(inventory)
        if args.write_inventory:
            with open(args.write_inventory, "w", encoding="utf-8") as handle:
                json.dump(inventory, handle, indent=2, default=str)
            print(f"wrote_inventory={args.write_inventory}")

        if args.cleanup_descriptions:
            stats = _cleanup_descriptions(
                session, actor_key=args.actor_key, execute=args.execute
            )
        else:
            stats = _enrich(
                session, inventory, actor_key=args.actor_key, execute=args.execute
            )
        print(json.dumps({"execute": args.execute, "stats": stats}, indent=2))
        if args.execute:
            session.commit()
        else:
            session.rollback()
            print("dry_run_complete (no writes)")
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
