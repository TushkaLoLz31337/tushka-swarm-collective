import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tushka.records import create_lifecycle_event, create_record, validate_lifecycle_event, validate_record

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "v1"


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class GovernedRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record_schema = load_json(SPEC / "record-envelope.schema.json")
        cls.event_schema = load_json(SPEC / "lifecycle-event.schema.json")
        Draft202012Validator.check_schema(cls.record_schema)
        Draft202012Validator.check_schema(cls.event_schema)
        cls.record_validator = Draft202012Validator(cls.record_schema, format_checker=FormatChecker())
        cls.event_validator = Draft202012Validator(cls.event_schema, format_checker=FormatChecker())

    def test_examples_validate_against_schema_and_runtime_contract(self):
        record = load_json(SPEC / "examples" / "record-public.json")
        event = load_json(SPEC / "examples" / "lifecycle-created.json")
        self.record_validator.validate(record)
        self.event_validator.validate(event)
        validate_record(record)
        validate_lifecycle_event(event)

    def test_factory_uses_random_uuid4_and_metadata_only(self):
        args = {
            "record_type": "task",
            "creator": {"actor_type": "agent", "identifier": "worker-a"},
            "origin": {"origin_type": "local"},
            "purpose": "orchestration",
            "classification": "private",
            "retention_class": "task",
            "content_ref": "local://private/tasks/task-1",
            "tags": [{"key": "scope", "value": "private"}],
        }
        first, second = create_record(**args), create_record(**args)
        self.assertNotEqual(first["record_id"], second["record_id"])
        self.assertNotIn("content", first)
        self.record_validator.validate(first)
        validate_record(second)

    def test_unknown_fields_and_unknown_tags_fail_closed(self):
        record = load_json(SPEC / "examples" / "record-public.json")
        record["permission"] = "admin"
        self.assertFalse(self.record_validator.is_valid(record))
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            validate_record(record)
        record = load_json(SPEC / "examples" / "record-public.json")
        record["tags"].append({"key": "scope", "value": "admin"})
        self.assertFalse(self.record_validator.is_valid(record))
        with self.assertRaisesRegex(ValueError, "controlled vocabulary"):
            validate_record(record)

    def test_bad_digest_and_non_v4_identifier_are_rejected(self):
        record = load_json(SPEC / "examples" / "record-public.json")
        record["content_digest"] = "sha256:not-a-digest"
        with self.assertRaisesRegex(ValueError, "sha256"):
            validate_record(record)
        record = load_json(SPEC / "examples" / "record-public.json")
        record["record_id"] = "00000000-0000-0000-0000-000000000000"
        with self.assertRaisesRegex(ValueError, "UUIDv4"):
            validate_record(record)

    def test_all_relationship_and_event_record_ids_require_uuid4(self):
        record = load_json(SPEC / "examples" / "record-public.json")
        record["relationships"] = [
            {
                "relationship_type": "cites",
                "target_record_id": "00000000-0000-0000-0000-000000000000",
            }
        ]
        self.assertFalse(self.record_validator.is_valid(record))
        with self.assertRaisesRegex(ValueError, "UUIDv4"):
            validate_record(record)

        event = load_json(SPEC / "examples" / "lifecycle-created.json")
        event["record_id"] = "00000000-0000-0000-0000-000000000000"
        self.assertFalse(self.event_validator.is_valid(event))
        with self.assertRaisesRegex(ValueError, "UUIDv4"):
            validate_lifecycle_event(event)

    def test_payload_and_free_text_event_reason_are_rejected(self):
        record = load_json(SPEC / "examples" / "record-public.json")
        record["payload"] = "not metadata"
        self.assertFalse(self.record_validator.is_valid(record))
        event = load_json(SPEC / "examples" / "lifecycle-created.json")
        event["reason"] = "free-form personal information"
        self.assertFalse(self.event_validator.is_valid(event))
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            validate_lifecycle_event(event)

    def test_lifecycle_factory_is_payload_free(self):
        record = load_json(SPEC / "examples" / "record-public.json")
        event = create_lifecycle_event(record_id=record["record_id"], event_type="payload_deleted", actor={"actor_type": "service"}, reason_code="retention_expired")
        self.event_validator.validate(event)
        validate_lifecycle_event(event)
        self.assertNotIn("payload", event)


if __name__ == "__main__":
    unittest.main()
