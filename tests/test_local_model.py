import asyncio
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar

from tushka.core import Task
from tushka.local_model import MAX_PROMPT_BYTES, MAX_RESPONSE_BYTES, LocalModelAgent


class LocalModelHandler(BaseHTTPRequestHandler):
    response_payload: ClassVar[dict[str, dict[str, str]]] = {"message": {"content": "local answer"}}
    raw_response = None
    request_payload = None
    request_path = None
    status_code = 200
    delay_seconds = 0
    redirect_location = None

    def do_POST(self):
        type(self).request_path = self.path
        length = int(self.headers.get("Content-Length", "0"))
        type(self).request_payload = json.loads(self.rfile.read(length))
        if type(self).delay_seconds:
            time.sleep(type(self).delay_seconds)
        body = type(self).raw_response
        if body is None:
            body = json.dumps(type(self).response_payload).encode("utf-8")
        self.send_response(type(self).status_code)
        self.send_header("Content-Type", "application/json")
        if type(self).redirect_location:
            self.send_header("Location", type(self).redirect_location)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        return


class LocalModelAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), LocalModelHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        LocalModelHandler.response_payload = {"message": {"content": "local answer"}}
        LocalModelHandler.raw_response = None
        LocalModelHandler.request_payload = None
        LocalModelHandler.request_path = None
        LocalModelHandler.status_code = 200
        LocalModelHandler.delay_seconds = 0
        LocalModelHandler.redirect_location = None

    def test_sends_prompt_and_returns_attributed_result(self):
        agent = LocalModelAgent("local-one", "test-model", self.base_url)
        result = asyncio.run(agent.run(Task("task-1", "Explain the test.")))
        self.assertEqual(result.agent_name, "local-one")
        self.assertEqual(result.content, "local answer")
        self.assertEqual(LocalModelHandler.request_payload["model"], "test-model")
        self.assertEqual(
            LocalModelHandler.request_payload["messages"],
            [{"role": "user", "content": "Explain the test."}],
        )
        self.assertFalse(LocalModelHandler.request_payload["stream"])
        self.assertEqual(LocalModelHandler.request_path, "/api/chat")

    def test_base_url_path_prefix_is_preserved(self):
        agent = LocalModelAgent(
            "local-one", "test-model", f"{self.base_url}/ollama/v1/"
        )
        asyncio.run(agent.run(Task("task-prefix", "hello")))
        self.assertEqual(LocalModelHandler.request_path, "/ollama/v1/api/chat")

    def test_rejects_prompt_over_1_mib_before_request(self):
        agent = LocalModelAgent("local-one", "test-model", self.base_url)
        prompt = "x" * (MAX_PROMPT_BYTES + 1)
        with self.assertRaisesRegex(RuntimeError, "1 MiB limit"):
            asyncio.run(agent.run(Task("task-large-prompt", prompt)))
        self.assertIsNone(LocalModelHandler.request_path)

    def test_rejects_response_over_4_mib(self):
        LocalModelHandler.raw_response = b"x" * (MAX_RESPONSE_BYTES + 1)
        agent = LocalModelAgent("local-one", "test-model", self.base_url)
        with self.assertRaisesRegex(RuntimeError, "4 MiB limit"):
            asyncio.run(agent.run(Task("task-large-response", "hello")))

    def test_request_timeout_is_reported(self):
        LocalModelHandler.delay_seconds = 0.2
        agent = LocalModelAgent(
            "local-one", "test-model", self.base_url, request_timeout_seconds=0.05
        )
        with self.assertRaisesRegex(RuntimeError, "timed out"):
            asyncio.run(agent.run(Task("task-timeout", "hello")))

    def test_does_not_follow_endpoint_redirects(self):
        LocalModelHandler.status_code = 302
        LocalModelHandler.redirect_location = f"{self.base_url}/redirect-target"
        agent = LocalModelAgent("local-one", "test-model", self.base_url)
        with self.assertRaisesRegex(RuntimeError, "HTTP 302"):
            asyncio.run(agent.run(Task("task-redirect", "private prompt")))
        self.assertEqual(LocalModelHandler.request_path, "/api/chat")

    def test_rejects_missing_message_content(self):
        LocalModelHandler.response_payload = {"message": {"content": ""}}
        agent = LocalModelAgent("local-one", "test-model", self.base_url)
        with self.assertRaisesRegex(RuntimeError, "no usable message content"):
            asyncio.run(agent.run(Task("task-2", "hello")))

    def test_rejects_invalid_json(self):
        LocalModelHandler.raw_response = b"not-json"
        agent = LocalModelAgent("local-one", "test-model", self.base_url)
        with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
            asyncio.run(agent.run(Task("task-3", "hello")))

    def test_reports_http_error_without_response_body(self):
        LocalModelHandler.status_code = 500
        agent = LocalModelAgent("local-one", "test-model", self.base_url)
        with self.assertRaisesRegex(RuntimeError, "HTTP 500"):
            asyncio.run(agent.run(Task("task-4", "hello")))

    def test_rejects_invalid_base_url(self):
        with self.assertRaises(ValueError):
            LocalModelAgent("local-one", "test-model", "file:///tmp/model")

    def test_rejects_plaintext_non_loopback_endpoint(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            LocalModelAgent("local-one", "test-model", "http://192.0.2.10:11434")

    def test_rejects_url_credentials(self):
        with self.assertRaises(ValueError):
            LocalModelAgent(
                "local-one", "test-model", "http://user:password@127.0.0.1:11434"
            )

    def test_rejects_non_finite_timeout(self):
        with self.assertRaises(ValueError):
            LocalModelAgent("local-one", "test-model", request_timeout_seconds=float("inf"))

    def test_rejects_empty_identity_or_model(self):
        with self.assertRaises(ValueError):
            LocalModelAgent("", "test-model")
        with self.assertRaises(ValueError):
            LocalModelAgent("local-one", "")


if __name__ == "__main__":
    unittest.main()



