import asyncio
import unittest
from datetime import UTC, datetime, timedelta

from tushka.broker import (
    AdmissionStatus,
    LocalBroker,
    TaskState,
    WorkerRegistration,
)
from tushka.core import AgentResult, Task


class StubWorker:
    def __init__(self, name, content="answer", capabilities=(), gate=None):
        self.name = name
        self.content = content
        self.capabilities = frozenset(capabilities)
        self.gate = gate
        self.started = asyncio.Event()
        self.calls = 0

    async def run(self, task):
        self.calls += 1
        self.started.set()
        if self.gate is not None:
            await self.gate.wait()
        return AgentResult(self.name, self.content)


class LocalBrokerTests(unittest.IsolatedAsyncioTestCase):
    async def test_acknowledges_and_tracks_successful_lifecycle(self):
        worker = StubWorker("docs", capabilities={"summarize"})
        broker = LocalBroker([WorkerRegistration(worker, frozenset({"summarize"}))])
        await broker.start()
        try:
            admission = broker.submit(
                Task("task-1", "private prompt"),
                required_capabilities=("summarize",),
                idempotency_key="request-1",
            )
            self.assertEqual(admission.status, AdmissionStatus.ACCEPTED)
            snapshot = await broker.wait("task-1")
            self.assertEqual(snapshot.state, TaskState.SUCCEEDED)
            self.assertEqual(snapshot.assigned_worker, "docs")
            self.assertEqual(snapshot.result.content, "answer")
            self.assertEqual(
                [event.state for event in snapshot.events],
                [
                    TaskState.CREATED,
                    TaskState.ACCEPTED,
                    TaskState.QUEUED,
                    TaskState.ASSIGNED,
                    TaskState.RUNNING,
                    TaskState.SUCCEEDED,
                ],
            )
            self.assertFalse(hasattr(snapshot, "prompt"))
        finally:
            await broker.close()

    async def test_routes_only_to_worker_with_required_capability(self):
        general = StubWorker("general", capabilities={"chat"})
        specialist = StubWorker("specialist", capabilities={"summarize"})
        broker = LocalBroker(
            [
                WorkerRegistration(general, frozenset({"chat"})),
                WorkerRegistration(specialist, frozenset({"summarize"})),
            ]
        )
        await broker.start()
        try:
            admission = broker.submit(
                Task("task-route", "summarize this"),
                required_capabilities=("summarize",),
            )
            self.assertEqual(admission.status, AdmissionStatus.ACCEPTED)
            result = await broker.wait("task-route")
            self.assertEqual(result.assigned_worker, "specialist")
            self.assertEqual(general.calls, 0)
            self.assertEqual(specialist.calls, 1)
        finally:
            await broker.close()

    async def test_rejects_when_no_worker_has_required_capabilities(self):
        worker = StubWorker("general", capabilities={"chat"})
        broker = LocalBroker([WorkerRegistration(worker, frozenset({"chat"}))])
        await broker.start()
        try:
            result = broker.submit(
                Task("task-no-route", "do work"),
                required_capabilities=("vision",),
            )
            self.assertEqual(result.status, AdmissionStatus.REJECTED)
            self.assertEqual(result.reason, "no_capable_worker")
            self.assertEqual(worker.calls, 0)
        finally:
            await broker.close()

    async def test_queue_pressure_returns_deferred_with_retry_guidance(self):
        gate = asyncio.Event()
        worker = StubWorker("slow", gate=gate)
        broker = LocalBroker(
            [WorkerRegistration(worker)],
            max_queued_tasks=1,
            retry_after_seconds=0.25,
        )
        await broker.start()
        try:
            first = broker.submit(Task("task-running", "one"))
            self.assertEqual(first.status, AdmissionStatus.ACCEPTED)
            await worker.started.wait()

            second = broker.submit(Task("task-queued", "two"))
            third = broker.submit(Task("task-deferred", "three"))
            self.assertEqual(second.status, AdmissionStatus.ACCEPTED)
            self.assertEqual(third.status, AdmissionStatus.DEFERRED)
            self.assertEqual(third.reason, "queue_capacity")
            self.assertEqual(third.retry_after_seconds, 0.25)

            gate.set()
            await broker.wait("task-running")
            await broker.wait("task-queued")
        finally:
            gate.set()
            await broker.close()

    async def test_idempotency_prevents_duplicate_execution(self):
        worker = StubWorker("worker")
        broker = LocalBroker([WorkerRegistration(worker)])
        await broker.start()
        try:
            task = Task("task-idempotent", "same request")
            first = broker.submit(task, idempotency_key="stable-key")
            duplicate = broker.submit(task, idempotency_key="stable-key")
            conflict = broker.submit(
                Task("task-conflict", "different request"),
                idempotency_key="stable-key",
            )
            self.assertEqual(first.status, AdmissionStatus.ACCEPTED)
            self.assertTrue(duplicate.duplicate)
            self.assertEqual(duplicate.task_id, "task-idempotent")
            self.assertEqual(conflict.status, AdmissionStatus.REJECTED)
            self.assertEqual(conflict.reason, "idempotency_key_conflict")
            await broker.wait("task-idempotent")
            self.assertEqual(worker.calls, 1)
        finally:
            await broker.close()

    async def test_cancels_queued_task_without_running_it(self):
        gate = asyncio.Event()
        worker = StubWorker("worker", gate=gate)
        broker = LocalBroker([WorkerRegistration(worker)], max_queued_tasks=2)
        await broker.start()
        try:
            broker.submit(Task("task-blocker", "first"))
            await worker.started.wait()
            broker.submit(Task("task-cancelled", "second"))
            self.assertTrue(broker.cancel("task-cancelled"))
            gate.set()
            await broker.wait("task-blocker")
            cancelled = await broker.wait("task-cancelled")
            self.assertEqual(cancelled.state, TaskState.CANCELLED)
            self.assertEqual(worker.calls, 1)
            self.assertFalse(broker.cancel("task-cancelled"))
        finally:
            gate.set()
            await broker.close()

    async def test_rejects_naive_or_expired_deadlines(self):
        worker = StubWorker("worker")
        broker = LocalBroker([WorkerRegistration(worker)])
        await broker.start()
        try:
            naive = broker.submit(
                Task("task-naive", "work"),
                deadline_at=datetime.now() + timedelta(seconds=10),
            )
            expired = broker.submit(
                Task("task-expired", "work"),
                deadline_at=datetime.now(UTC) - timedelta(seconds=1),
            )
            self.assertEqual(naive.reason, "deadline_must_be_timezone_aware")
            self.assertEqual(expired.reason, "deadline_expired")
        finally:
            await broker.close()

    async def test_running_cancellation_does_not_kill_worker_loop(self):
        gate = asyncio.Event()

        class FirstTaskBlocksWorker(StubWorker):
            async def run(self, task):
                self.calls += 1
                self.started.set()
                if task.task_id == "task-cancel-running":
                    await gate.wait()
                return AgentResult(self.name, "completed")

        worker = FirstTaskBlocksWorker("worker")
        broker = LocalBroker([WorkerRegistration(worker)])
        await broker.start()
        try:
            broker.submit(Task("task-cancel-running", "first"))
            await worker.started.wait()
            self.assertTrue(broker.cancel("task-cancel-running"))
            cancelled = await broker.wait("task-cancel-running")
            self.assertEqual(cancelled.state, TaskState.CANCELLED)

            next_admission = broker.submit(Task("task-after-cancel", "second"))
            self.assertEqual(next_admission.status, AdmissionStatus.ACCEPTED)
            completed = await asyncio.wait_for(
                broker.wait("task-after-cancel"), timeout=1
            )
            self.assertEqual(completed.state, TaskState.SUCCEEDED)
            self.assertEqual(worker.calls, 2)
        finally:
            gate.set()
            await broker.close()

    async def test_worker_failure_exposes_only_stable_error_code(self):
        class FailingWorker(StubWorker):
            async def run(self, task):
                self.calls += 1
                raise RuntimeError("sensitive-token-must-not-leak")

        worker = FailingWorker("worker")
        broker = LocalBroker([WorkerRegistration(worker)])
        await broker.start()
        try:
            broker.submit(Task("task-failure", "work"))
            failed = await broker.wait("task-failure")
            self.assertEqual(failed.state, TaskState.FAILED)
            self.assertEqual(failed.error_code, "worker_error")
            self.assertNotIn(
                "sensitive-token-must-not-leak",
                repr(failed.events),
            )
        finally:
            await broker.close()

    async def test_history_pruning_preserves_cancelled_items_still_in_queue(self):
        gate = asyncio.Event()
        worker = StubWorker("worker", gate=gate)
        broker = LocalBroker(
            [WorkerRegistration(worker)],
            max_queued_tasks=2,
            max_record_history=2,
        )
        await broker.start()
        try:
            broker.submit(Task("task-active", "first"))
            await worker.started.wait()
            broker.submit(Task("task-cancelled-pending", "second"))
            self.assertTrue(broker.cancel("task-cancelled-pending"))

            deferred = broker.submit(Task("task-not-yet-admitted", "third"))
            self.assertEqual(deferred.status, AdmissionStatus.DEFERRED)
            self.assertEqual(deferred.reason, "record_history_capacity")

            gate.set()
            await broker.wait("task-active")
            await broker.wait("task-cancelled-pending")

            accepted = broker.submit(Task("task-not-yet-admitted", "third"))
            self.assertEqual(accepted.status, AdmissionStatus.ACCEPTED)
            result = await broker.wait("task-not-yet-admitted")
            self.assertEqual(result.state, TaskState.SUCCEEDED)
        finally:
            gate.set()
            await broker.close()

    async def test_close_cancels_running_work(self):
        gate = asyncio.Event()
        worker = StubWorker("worker", gate=gate)
        broker = LocalBroker([WorkerRegistration(worker)])
        await broker.start()
        broker.submit(Task("task-close", "work"))
        await worker.started.wait()
        await broker.close()
        snapshot = broker.get_record("task-close")
        self.assertEqual(snapshot.state, TaskState.CANCELLED)


if __name__ == "__main__":
    unittest.main()
