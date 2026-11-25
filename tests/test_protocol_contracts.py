import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "v1"
MAX_PROMPT_UTF8_BYTES = 65_536


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_task(task):
    """Validate the v1 task schema and its UTF-8 byte-size contract."""
    Draft202012Validator(load_json(SPEC / "task.schema.json")).validate(task)
    prompt_size = len(task["prompt"].encode("utf-8"))
    if prompt_size > MAX_PROMPT_UTF8_BYTES:
        raise ValueError(
            f"prompt is {prompt_size} UTF-8 bytes; maximum is {MAX_PROMPT_UTF8_BYTES}"
        )


class ProtocolContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task_schema = load_json(SPEC / "task.schema.json")
        cls.result_schema = load_json(SPEC / "result.schema.json")
        cls.task_validator = Draft202012Validator(cls.task_schema)
        cls.result_validator = Draft202012Validator(cls.result_schema)

    def test_schemas_are_valid_draft_2020_12_schemas(self):
        Draft202012Validator.check_schema(self.task_schema)
        Draft202012Validator.check_schema(self.result_schema)

    def test_all_examples_validate_against_their_schemas(self):
        self.task_validator.validate(load_json(SPEC / "examples" / "task.json"))
        self.result_validator.validate(
            load_json(SPEC / "examples" / "result-success.json")
        )
        self.result_validator.validate(
            load_json(SPEC / "examples" / "result-failure.json")
        )

    def test_task_rejects_unsupported_version_and_unknown_fields(self):
        task = load_json(SPEC / "examples" / "task.json")
        for field, value in (
            ("protocol_version", "2.0"),
            ("unexpected", True),
        ):
            with self.subTest(field=field):
                invalid = dict(task)
                invalid[field] = value
                self.assertFalse(self.task_validator.is_valid(invalid))

    def test_result_rejects_unsupported_version_unknown_fields_and_status(self):
        result = load_json(SPEC / "examples" / "result-success.json")
        cases = (
            ("unsupported version", {"protocol_version": "2.0"}),
            ("unknown field", {"unexpected": True}),
            ("invalid status", {"status": "pending"}),
        )
        for label, change in cases:
            with self.subTest(case=label):
                invalid = dict(result)
                invalid.update(change)
                self.assertFalse(self.result_validator.is_valid(invalid))

    def test_success_requires_content(self):
        result = load_json(SPEC / "examples" / "result-success.json")
        result.pop("content")
        self.assertFalse(self.result_validator.is_valid(result))

    def test_success_rejects_error_object(self):
        result = load_json(SPEC / "examples" / "result-success.json")
        result["error"] = {"code": "CONTRADICTION", "message": "not allowed"}
        self.assertFalse(self.result_validator.is_valid(result))

    def test_failure_requires_error_and_rejects_success_content(self):
        result = load_json(SPEC / "examples" / "result-failure.json")
        result.pop("error")
        self.assertFalse(self.result_validator.is_valid(result))

        result = load_json(SPEC / "examples" / "result-failure.json")
        result["content"] = "Contradictory success payload"
        self.assertFalse(self.result_validator.is_valid(result))

    def test_malformed_error_fields_are_rejected(self):
        base = load_json(SPEC / "examples" / "result-failure.json")
        malformed = (
            {"message": "missing code"},
            {"code": "", "message": "empty code"},
            {"code": "E", "message": ""},
            {"code": "E", "message": "bad retry flag", "retryable": "yes"},
            {"code": "E", "message": "unknown nested field", "extra": 1},
            {"code": 42, "message": "code must be a string"},
            {"code": "E", "message": 42},
        )
        for error in malformed:
            with self.subTest(error=error):
                invalid = dict(base)
                invalid["error"] = error
                self.assertFalse(self.result_validator.is_valid(invalid))

    def test_prompt_limit_is_inclusive_utf8_bytes(self):
        task = load_json(SPEC / "examples" / "task.json")
        task["prompt"] = "a" * MAX_PROMPT_UTF8_BYTES
        validate_task(task)

        task["prompt"] = "a" * (MAX_PROMPT_UTF8_BYTES + 1)
        with self.assertRaises(ValueError):
            validate_task(task)

    def test_prompt_limit_counts_utf8_bytes_not_characters(self):
        task = load_json(SPEC / "examples" / "task.json")
        task["prompt"] = "é" * (MAX_PROMPT_UTF8_BYTES // 2)
        self.assertEqual(len(task["prompt"]), MAX_PROMPT_UTF8_BYTES // 2)
        self.assertEqual(len(task["prompt"].encode("utf-8")), MAX_PROMPT_UTF8_BYTES)
        validate_task(task)

        task["prompt"] += "é"
        with self.assertRaises(ValueError):
            validate_task(task)


if __name__ == "__main__":
    unittest.main()
