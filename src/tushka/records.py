"""Local-first governed record metadata; persistence and authorization are separate layers."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import UUID, uuid4

SCHEMA_VERSION = "1.0"
RECORD_TYPES = frozenset({"task", "decision", "source", "artifact", "checkpoint", "conversation_summary", "experiment", "policy", "use_case"})
PURPOSES = frozenset({"orchestration", "continuity", "research", "build", "audit", "governance", "interoperability"})
CLASSIFICATIONS = frozenset({"public", "community", "private", "confidential", "restricted"})
RETENTION_CLASSES = frozenset({"ephemeral", "task", "project", "provenance", "security", "legal_hold"})
REVIEW_STATES = frozenset({"unreviewed", "reviewed", "verified", "disputed", "superseded", "withdrawn"})
ACTOR_TYPES = frozenset({"human", "agent", "node", "service"})
ORIGIN_TYPES = frozenset({"local", "repository", "url", "generated"})
RELATIONSHIP_TYPES = frozenset({"derived_from", "cites", "corrects", "supersedes", "replies_to", "attached_to"})
EVENT_TYPES = frozenset({"created", "validated", "reviewed", "superseded", "corrected", "tombstoned", "payload_deleted", "retention_expired", "exported"})
TAG_VALUES = {
    "type": RECORD_TYPES,
    "domain": frozenset({"orchestration", "continuity", "security", "protocol", "governance", "research", "build", "integration"}),
    "state": frozenset({"proposed", "verified", "disputed"}),
    "scope": frozenset({"private", "community", "public"}),
    "retention": frozenset({"ephemeral", "project", "provenance", "security", "legal_hold"}),
}
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REASON_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def _object(value: Any, name: str, allowed: set[str], required: set[str]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    keys = set(value)
    if keys - allowed:
        raise ValueError(f"{name} contains unsupported fields")
    if required - keys:
        raise ValueError(f"{name} is missing required fields")


def _enum(value: Any, choices: frozenset[str], name: str) -> None:
    if not isinstance(value, str) or value not in choices:
        raise ValueError(f"{name} is not an allowed value")


def _uuid4(value: Any, name: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a UUID string")
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError):
        raise ValueError(f"{name} must be a UUID string") from None
    if parsed.version != 4:
        raise ValueError(f"{name} must be a random UUIDv4")


def _timestamp(value: Any, name: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")


def _actor(actor: Any, name: str) -> None:
    _object(actor, name, {"actor_type", "identifier"}, {"actor_type"})
    _enum(actor["actor_type"], ACTOR_TYPES, f"{name}.actor_type")
    if "identifier" in actor and (not isinstance(actor["identifier"], str) or not actor["identifier"] or len(actor["identifier"]) > 128):
        raise ValueError(f"{name}.identifier must be a non-empty string of at most 128 characters")


def validate_record(record: Mapping[str, Any]) -> None:
    """Validate v1 metadata without reading or retaining the referenced payload."""
    required = {"record_id", "record_type", "schema_version", "created_at", "creator", "origin", "purpose", "classification", "license", "retention_class", "content_ref", "review_state", "tags", "relationships"}
    allowed = required | {"content_digest"}
    _object(record, "record", allowed, required)
    _uuid4(record["record_id"], "record_id")
    _enum(record["record_type"], RECORD_TYPES, "record_type")
    if record["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported schema_version")
    _timestamp(record["created_at"], "created_at")
    _actor(record["creator"], "creator")
    origin = record["origin"]
    _object(origin, "origin", {"origin_type", "uri", "revision"}, {"origin_type"})
    _enum(origin["origin_type"], ORIGIN_TYPES, "origin.origin_type")
    for key, limit in (("uri", 2048), ("revision", 256)):
        if key in origin and (not isinstance(origin[key], str) or not origin[key] or len(origin[key]) > limit):
            raise ValueError(f"origin.{key} must be a non-empty bounded string")
    _enum(record["purpose"], PURPOSES, "purpose")
    _enum(record["classification"], CLASSIFICATIONS, "classification")
    _enum(record["retention_class"], RETENTION_CLASSES, "retention_class")
    _enum(record["review_state"], REVIEW_STATES, "review_state")
    if not isinstance(record["license"], str) or not record["license"] or len(record["license"]) > 128:
        raise ValueError("license must be a non-empty SPDX identifier or NOASSERTION")
    if not isinstance(record["content_ref"], str) or not record["content_ref"] or len(record["content_ref"]) > 2048:
        raise ValueError("content_ref must be a non-empty bounded reference")
    if "content_digest" in record and (not isinstance(record["content_digest"], str) or not _DIGEST_RE.fullmatch(record["content_digest"])):
        raise ValueError("content_digest must be a sha256 digest")
    tags = record["tags"]
    if not isinstance(tags, list) or len(tags) > 32:
        raise ValueError("tags must be a list of at most 32 controlled tags")
    seen: set[tuple[str, str]] = set()
    for tag in tags:
        _object(tag, "tag", {"key", "value"}, {"key", "value"})
        key, value = tag["key"], tag["value"]
        if key not in TAG_VALUES or not isinstance(value, str) or value not in TAG_VALUES[key]:
            raise ValueError("tag key/value is not in the controlled vocabulary")
        if (key, value) in seen:
            raise ValueError("duplicate tag")
        seen.add((key, value))
    relationships = record["relationships"]
    if not isinstance(relationships, list) or len(relationships) > 64:
        raise ValueError("relationships must be a list of at most 64 entries")
    for item in relationships:
        _object(item, "relationship", {"relationship_type", "target_record_id"}, {"relationship_type", "target_record_id"})
        _enum(item["relationship_type"], RELATIONSHIP_TYPES, "relationship.relationship_type")
        _uuid4(item["target_record_id"], "target_record_id")


def validate_lifecycle_event(event: Mapping[str, Any]) -> None:
    """Validate a payload-free lifecycle event."""
    required = {"event_id", "record_id", "schema_version", "event_type", "occurred_at", "actor"}
    _object(event, "event", required | {"reason_code", "related_record_id"}, required)
    _uuid4(event["event_id"], "event_id")
    _uuid4(event["record_id"], "record_id")
    if event["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported schema_version")
    _enum(event["event_type"], EVENT_TYPES, "event_type")
    _timestamp(event["occurred_at"], "occurred_at")
    _actor(event["actor"], "actor")
    if "reason_code" in event and (not isinstance(event["reason_code"], str) or not _REASON_RE.fullmatch(event["reason_code"])):
        raise ValueError("reason_code must be a bounded machine-readable code")
    if "related_record_id" in event:
        _uuid4(event["related_record_id"], "related_record_id")


def create_record(*, record_type: str, creator: Mapping[str, Any], origin: Mapping[str, Any], purpose: str, classification: str, retention_class: str, content_ref: str, license: str = "NOASSERTION", content_digest: str | None = None, review_state: str = "unreviewed", tags: list[Mapping[str, str]] | None = None, relationships: list[Mapping[str, str]] | None = None) -> dict[str, Any]:
    """Create a validated metadata envelope with a random ID unrelated to personal data."""
    record: dict[str, Any] = {
        "record_id": str(uuid4()), "record_type": record_type, "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "creator": dict(creator), "origin": dict(origin), "purpose": purpose,
        "classification": classification, "license": license, "retention_class": retention_class,
        "content_ref": content_ref, "review_state": review_state,
        "tags": [dict(tag) for tag in (tags or [])],
        "relationships": [dict(item) for item in (relationships or [])],
    }
    if content_digest is not None:
        record["content_digest"] = content_digest
    validate_record(record)
    return record


def create_lifecycle_event(*, record_id: str, event_type: str, actor: Mapping[str, Any], reason_code: str | None = None, related_record_id: str | None = None) -> dict[str, Any]:
    """Create a validated metadata-only event; persistence is a separate layer."""
    event: dict[str, Any] = {
        "event_id": str(uuid4()), "record_id": record_id, "schema_version": SCHEMA_VERSION,
        "event_type": event_type,
        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "actor": dict(actor),
    }
    if reason_code is not None:
        event["reason_code"] = reason_code
    if related_record_id is not None:
        event["related_record_id"] = related_record_id
    validate_lifecycle_event(event)
    return event
