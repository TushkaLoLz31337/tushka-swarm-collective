import asyncio
import unittest

from tushka.core import AgentResult, Coordinator, Task


class StubAgent:
    def __init__(self, name, content="", error=None, delay=0):
        self.name = name
        self.content = content
        self.error = error
        self.delay = delay

    async def run(self, task):
        await asyncio.sleep(self.delay)
        if self.error:
            raise RuntimeError(self.error)
        return AgentResult(self.name, self.content)


class CoordinatorTests(unittest.TestCase):
    def test_collects_multiple_agents(self):
        coordinator = Coordinator(
            [
                StubAgent("alpha", "first"),
                StubAgent("beta", "second"),
            ]
        )
        results = asyncio.run(coordinator.run(Task("t1", "hello")))
        self.assertEqual([r.agent_name for r in results], ["alpha", "beta"])
        self.assertTrue(all(r.success for r in results))

    def test_isolates_agent_failure_without_exposing_exception_text(self):
        coordinator = Coordinator(
            [
                StubAgent("working", "usable answer"),
                StubAgent("broken", error="secret-token-must-not-appear"),
            ]
        )
        results = asyncio.run(coordinator.run(Task("t2", "hello")))
        self.assertTrue(results[0].success)
        self.assertFalse(results[1].success)
        combined = coordinator.synthesize(results)
        self.assertIn("usable answer", combined)
        self.assertIn("RuntimeError", combined)
        self.assertNotIn("secret-token-must-not-appear", combined)

    def test_synthesis_rejects_no_usable_results(self):
        with self.assertRaises(RuntimeError):
            Coordinator.synthesize(
                [
                    AgentResult("empty", "", success=True),
                    AgentResult("failed", "", success=False, error="offline"),
                ]
            )

    def test_requires_agents(self):
        with self.assertRaises(ValueError):
            Coordinator([])

    def test_rejects_duplicate_agent_names(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            Coordinator([StubAgent("same"), StubAgent("same")])

    def test_rejects_non_finite_timeout(self):
        with self.assertRaises(ValueError):
            Coordinator([StubAgent("alpha")], timeout_seconds=float("inf"))

    def test_task_requires_identifier_and_prompt(self):
        with self.assertRaises(ValueError):
            Task("", "hello")
        with self.assertRaises(ValueError):
            Task("t1", " ")

    def test_timeout_is_reported(self):
        coordinator = Coordinator(
            [StubAgent("slow", "late", delay=0.05)], timeout_seconds=0.001
        )
        results = asyncio.run(coordinator.run(Task("t3", "hello")))
        self.assertFalse(results[0].success)
        self.assertIn("Timed out", results[0].error)


if __name__ == "__main__":
    unittest.main()
