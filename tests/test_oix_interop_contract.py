import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "v1"
FIXTURES = ROOT / "tests" / "fixtures"

OIX_BODY_FIELDS = {
    "protocol",
    "version",
    "message_id",
    "sender",
    "recipient",
    "type",
    "issued_at",
    "expires_at",
    "nonce",
    "requested_capability",
    "payload",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class OIXInteropContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task_validator = Draft202012Validator(
            load_json(SPEC / "task.schema.json")
        )
        cls.result_validator = Draft202012Validator(
            load_json(SPEC / "result.schema.json")
        )

    def validate_oix_wrapper_shape(self, envelope, expected_type):
        self.assertEqual(set(envelope), {"body", "signature"})
        self.assertIsInstance(envelope["signature"], str)
        self.assertGreaterEqual(len(envelope["signature"]), 80)
        self.assertLessEqual(len(envelope["signature"]), 100)

        body = envelope["body"]
        self.assertEqual(set(body), OIX_BODY_FIELDS)
        self.assertEqual(body["protocol"], "OIX")
        self.assertEqual(body["version"], "0.1")
        self.assertEqual(body["type"], expected_type)
        self.assertRegex(
            body["sender"],
            re.compile(r"^ed25519:[0-9a-f]{64}$"),
        )
        self.assertIsInstance(body["recipient"], str)
        self.assertGreaterEqual(len(body["recipient"]), 1)
        self.assertLessEqual(len(body["recipient"]), 256)
        self.assertIsInstance(body["message_id"], str)
        self.assertIsInstance(body["issued_at"], int)
        self.assertIsInstance(body["expires_at"], int)
        self.assertGreater(body["expires_at"], body["issued_at"])
        self.assertIsInstance(body["nonce"], str)
        self.assertGreaterEqual(len(body["nonce"]), 20)
        self.assertLessEqual(len(body["nonce"]), 128)
        self.assertIsInstance(body["requested_capability"], str)
        self.assertTrue(body["requested_capability"])
        self.assertIsInstance(body["payload"], dict)
        return body

    def test_tushka_task_payload_fits_oix_task_request_wrapper(self):
        envelope = load_json(FIXTURES / "oix-task-request.json")
        body = self.validate_oix_wrapper_shape(envelope, "task.request")

        self.task_validator.validate(body["payload"])
        self.assertEqual(body["payload"]["message_type"], "task")
        self.assertNotEqual(body["message_id"], body["payload"]["task_id"])
        self.assertEqual(body["requested_capability"], "summarize")

    def test_tushka_result_payload_fits_oix_task_result_wrapper(self):
        envelope = load_json(FIXTURES / "oix-task-result.json")
        body = self.validate_oix_wrapper_shape(envelope, "task.result")

        self.result_validator.validate(body["payload"])
        self.assertEqual(body["payload"]["message_type"], "result")
        self.assertNotEqual(body["message_id"], body["payload"]["task_id"])
        self.assertEqual(body["requested_capability"], "summarize")

    def test_tushka_payload_rejects_fields_outside_its_versioned_contract(self):
        envelope = load_json(FIXTURES / "oix-task-request.json")
        envelope["body"]["payload"]["capability"] = "summarize"
        body = self.validate_oix_wrapper_shape(envelope, "task.request")
        with self.assertRaises(Exception):
            self.task_validator.validate(body["payload"])


if __name__ == "__main__":
    unittest.main()
