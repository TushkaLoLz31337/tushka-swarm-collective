"""Bounded, in-process task broker for explicitly registered local agents.

This first broker is intentionally local-only. It does not provide network
transport, persistent storage, cross-node identity, or private-memory sharing.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import math
from typing import Sequence

from .core import Agent, AgentResult, Task


class AdmissionStatus(StrEnum):
    """Machine-readable result of a task admission request."""

    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class TaskState(StrEnum):
    """Observable task lifecycle states."""

    CREATED = "created"
    ACCEPTED = "accepted"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


_TERMINAL_STATES = {
    TaskState.SUCCEEDED,
    TaskState.FAILED,
    TaskState.CANCELLED,
    TaskState.EXPIRED,
}


@dataclass(frozen=True, slots=True)
class WorkerRegistration:
    """A local agent and the capabilities it explicitly offers."""

    agent: Agent
    capabilities: frozenset[str] = frozenset()
    node_id: str = "local"
    max_concurrency: int = 1

    def __post_init__(self) -> None:
        if not isinstance(getattr(self.agent, "name", None), str) or not self.agent.name.strip():
            raise ValueError("Worker agent must have a non-empty name.")
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("node_id must be a non-empty string.")
        if (
            not isinstance(self.max_concurrency, int)
            or isinstance(self.max_concurrency, bool)
            or self.max_concurrency < 1
        ):
            raise ValueError("max_concurrency must be a positive integer.")
        if any(not isinstance(item, str) or not item.strip() for item in self.capabilities):
            raise ValueError("Worker capabilities must be non-empty strings.")


@dataclass(frozen=True, slots=True)
class AdmissionResult:
    """Acknowledgement returned immediately after an admission attempt."""

    status: AdmissionStatus
    task_id: str
    reason: str | None = None
    retry_after_seconds: float | None = None
    duplicate: bool = False


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    """Minimal event metadata; task prompts and result payloads are excluded."""

    state: TaskState
    occurred_at: datetime
    worker_name: str | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class TaskSnapshot:
    """Read-only view of task state without exposing its submitted prompt."""

    task_id: str
    state: TaskState
    created_at: datetime
    updated_at: datetime
    assigned_worker: str | None
    result: AgentResult | None
    error_code: str | None
    events: tuple[LifecycleEvent, ...]


@dataclass(slots=True)
class _TaskRecord:
    task: Task
    required_capabilities: frozenset[str]
    idempotency_key: str | None
    deadline_at: datetime | None
    state: TaskState
    created_at: datetime
    updated_at: datetime
    assigned_worker: str | None = None
    result: AgentResult | None = None
    error_code: str | None = None
    events: list[LifecycleEvent] = field(default_factory=list)
    completed: asyncio.Event = field(default_factory=asyncio.Event)


class LocalBroker:
    """A bounded local broker with capability routing and lifecycle tracking.

    The queue and record history are bounded. Worker execution is limited by
    each registration's concurrency and by a shared per-node concurrency cap.
    Retries, durable persistence, remote transport, and cross-node auth are
    intentionally deferred to later milestones.
    """

    def __init__(
        self,
        workers: Sequence[WorkerRegistration],
        *,
        max_queued_tasks: int = 128,
        max_record_history: int = 10_000,
        per_node_concurrency: int = 1,
        retry_after_seconds: float = 1.0,
    ) -> None:
        if not workers:
            raise ValueError("LocalBroker requires at least one worker.")
        if len({worker.agent.name for worker in workers}) != len(workers):
            raise ValueError("Worker names must be unique.")
        for name, value in (
            ("max_queued_tasks", max_queued_tasks),
            ("max_record_history", max_record_history),
            ("per_node_concurrency", per_node_concurrency),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive integer.")
        if not math.isfinite(retry_after_seconds) or retry_after_seconds <= 0:
            raise ValueError("retry_after_seconds must be finite and positive.")

        self._workers = tuple(workers)
        self._queues = {
            worker.agent.name: asyncio.Queue(maxsize=max_queued_tasks)
            for worker in self._workers
        }
        self._worker_semaphores = {
            worker.agent.name: asyncio.Semaphore(worker.max_concurrency)
            for worker in self._workers
        }
        self._node_semaphores = {
            node_id: asyncio.Semaphore(per_node_concurrency)
            for node_id in {worker.node_id for worker in self._workers}
        }
        self._max_queued_tasks = max_queued_tasks
        self._max_record_history = max_record_history
        self._retry_after_seconds = retry_after_seconds
        self._records: OrderedDict[str, _TaskRecord] = OrderedDict()
        self._idempotency: dict[str, str] = {}
        self._queued_count = 0
        self._active_counts = {worker.agent.name: 0 for worker in self._workers}
        self._worker_tasks: list[asyncio.Task[None]] = []
        self._execution_tasks: dict[str, asyncio.Task[None]] = {}
        self._started = False
        self._closed = False
        self._route_cursor = 0

    async def start(self) -> None:
        """Start local worker loops. Must be called inside a running event loop."""
        if self._closed:
            raise RuntimeError("Broker is closed.")
        if self._started:
            return
        self._started = True
        for worker in self._workers:
            for _ in range(worker.max_concurrency):
                self._worker_tasks.append(
                    asyncio.create_task(
                        self._worker_loop(worker),
                        name=f"tushka-worker-{worker.agent.name}",
                    )
                )

    def submit(
        self,
        task: Task,
        *,
        required_capabilities: Sequence[str] = (),
        idempotency_key: str | None = None,
        deadline_at: datetime | None = None,
    ) -> AdmissionResult:
        """Admit a task without blocking; queue pressure returns DEFERRED."""
        if not isinstance(task, Task):
            raise TypeError("task must be a Task instance.")
        if self._closed or not self._started:
            return AdmissionResult(
                AdmissionStatus.REJECTED, task.task_id, "broker_not_running"
            )

        required = frozenset(required_capabilities)
        if any(not isinstance(item, str) or not item.strip() for item in required):
            return AdmissionResult(
                AdmissionStatus.REJECTED, task.task_id, "invalid_capability"
            )
        if idempotency_key is not None and (
            not isinstance(idempotency_key, str) or not idempotency_key.strip()
        ):
            return AdmissionResult(
                AdmissionStatus.REJECTED, task.task_id, "invalid_idempotency_key"
            )
        if deadline_at is not None:
            if deadline_at.tzinfo is None or deadline_at.utcoffset() is None:
                return AdmissionResult(
                    AdmissionStatus.REJECTED, task.task_id, "deadline_must_be_timezone_aware"
                )
            if deadline_at <= _now():
                return AdmissionResult(
                    AdmissionStatus.REJECTED, task.task_id, "deadline_expired"
                )

        if idempotency_key is not None and idempotency_key in self._idempotency:
            existing_id = self._idempotency[idempotency_key]
            existing = self._records.get(existing_id)
            if existing is not None:
                same_request = (
                    existing.task == task
                    and existing.required_capabilities == required
                    and existing.deadline_at == deadline_at
                )
                if not same_request:
                    return AdmissionResult(
                        AdmissionStatus.REJECTED,
                        task.task_id,
                        "idempotency_key_conflict",
                    )
                return AdmissionResult(
                    AdmissionStatus.ACCEPTED,
                    existing_id,
                    duplicate=True,
                )

        if task.task_id in self._records:
            return AdmissionResult(
                AdmissionStatus.REJECTED, task.task_id, "duplicate_task_id"
            )

        eligible = [
            worker
            for worker in self._workers
            if required.issubset(worker.capabilities)
        ]
        if not eligible:
            return AdmissionResult(
                AdmissionStatus.REJECTED, task.task_id, "no_capable_worker"
            )

        if self._queued_count >= self._max_queued_tasks:
            return AdmissionResult(
                AdmissionStatus.DEFERRED,
                task.task_id,
                "queue_capacity",
                retry_after_seconds=self._retry_after_seconds,
            )

        self._prune_history()
        if len(self._records) >= self._max_record_history:
            return AdmissionResult(
                AdmissionStatus.DEFERRED,
                task.task_id,
                "record_history_capacity",
                retry_after_seconds=self._retry_after_seconds,
            )

        worker = self._select_worker(eligible)
        now = _now()
        record = _TaskRecord(
            task=task,
            required_capabilities=required,
            idempotency_key=idempotency_key,
            deadline_at=deadline_at,
            state=TaskState.CREATED,
            created_at=now,
            updated_at=now,
        )
        record.events.append(LifecycleEvent(TaskState.CREATED, now))
        self._records[task.task_id] = record
        self._transition(record, TaskState.ACCEPTED)
        self._transition(record, TaskState.QUEUED)
        self._queues[worker.agent.name].put_nowait(task.task_id)
        self._queued_count += 1
        if idempotency_key is not None:
            self._idempotency[idempotency_key] = task.task_id
        return AdmissionResult(AdmissionStatus.ACCEPTED, task.task_id)

    def get_record(self, task_id: str) -> TaskSnapshot | None:
        """Return a task's current state and minimal lifecycle metadata."""
        record = self._records.get(task_id)
        return _snapshot(record) if record is not None else None

    async def wait(self, task_id: str) -> TaskSnapshot:
        """Wait for a task to reach a terminal state and return its snapshot."""
        record = self._records.get(task_id)
        if record is None:
            raise KeyError(task_id)
        await record.completed.wait()
        return _snapshot(record)

    def cancel(self, task_id: str) -> bool:
        """Cancel queued or running work. Returns false for unknown/terminal IDs."""
        record = self._records.get(task_id)
        if record is None or record.state in _TERMINAL_STATES:
            return False
        self._transition(record, TaskState.CANCELLED, error_code="cancelled")
        execution = self._execution_tasks.get(task_id)
        if execution is not None:
            execution.cancel()
        return True

    async def close(self) -> None:
        """Stop the broker and cancel outstanding local work."""
        if self._closed:
            return
        self._closed = True
        for record in self._records.values():
            if record.state not in _TERMINAL_STATES:
                self._transition(record, TaskState.CANCELLED, error_code="broker_closed")
                execution = self._execution_tasks.get(record.task.task_id)
                if execution is not None:
                    execution.cancel()
        for worker_task in self._worker_tasks:
            worker_task.cancel()
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

    async def _worker_loop(self, registration: WorkerRegistration) -> None:
        queue = self._queues[registration.agent.name]
        while not self._closed:
            task_id = await queue.get()
            self._queued_count -= 1
            record = self._records.get(task_id)
            if record is None or record.state in _TERMINAL_STATES:
                queue.task_done()
                continue

            self._active_counts[registration.agent.name] += 1
            execution = asyncio.create_task(
                self._execute(registration, record),
                name=f"tushka-task-{task_id}",
            )
            self._execution_tasks[task_id] = execution
            try:
                await execution
            except asyncio.CancelledError:
                if self._closed:
                    break
            finally:
                self._execution_tasks.pop(task_id, None)
                self._active_counts[registration.agent.name] -= 1
                queue.task_done()

    async def _execute(
        self, registration: WorkerRegistration, record: _TaskRecord
    ) -> None:
        async with self._worker_semaphores[registration.agent.name]:
            async with self._node_semaphores[registration.node_id]:
                if record.state in _TERMINAL_STATES:
                    return
                if record.deadline_at is not None and record.deadline_at <= _now():
                    self._transition(
                        record, TaskState.EXPIRED, error_code="deadline_expired"
                    )
                    return
                self._transition(
                    record, TaskState.ASSIGNED, worker_name=registration.agent.name
                )
                self._transition(
                    record, TaskState.RUNNING, worker_name=registration.agent.name
                )
                try:
                    if record.deadline_at is None:
                        result = await registration.agent.run(record.task)
                    else:
                        timeout = max(
                            0.0, (record.deadline_at - _now()).total_seconds()
                        )
                        result = await asyncio.wait_for(
                            registration.agent.run(record.task), timeout=timeout
                        )
                    if not isinstance(result, AgentResult):
                        self._transition(
                            record, TaskState.FAILED, error_code="invalid_worker_result"
                        )
                    elif result.agent_name != registration.agent.name:
                        self._transition(
                            record, TaskState.FAILED, error_code="worker_identity_mismatch"
                        )
                    elif not result.success:
                        record.result = AgentResult(
                            registration.agent.name, "", success=False
                        )
                        self._transition(
                            record, TaskState.FAILED, error_code="worker_failed"
                        )
                    else:
                        record.result = result
                        self._transition(record, TaskState.SUCCEEDED)
                except TimeoutError:
                    self._transition(
                        record, TaskState.EXPIRED, error_code="deadline_expired"
                    )
                except asyncio.CancelledError:
                    if record.state not in _TERMINAL_STATES:
                        self._transition(
                            record, TaskState.CANCELLED, error_code="cancelled"
                        )
                    raise
                except Exception:
                    self._transition(
                        record, TaskState.FAILED, error_code="worker_error"
                    )

    def _select_worker(
        self, eligible: Sequence[WorkerRegistration]
    ) -> WorkerRegistration:
        ordered = list(self._workers)
        start = self._route_cursor % len(ordered)
        rotated = ordered[start:] + ordered[:start]
        eligible_names = {worker.agent.name for worker in eligible}
        selected = min(
            (worker for worker in rotated if worker.agent.name in eligible_names),
            key=lambda worker: (
                self._queues[worker.agent.name].qsize()
                + self._active_counts[worker.agent.name],
                rotated.index(worker),
            ),
        )
        self._route_cursor = (ordered.index(selected) + 1) % len(ordered)
        return selected

    def _prune_history(self) -> None:
        while len(self._records) >= self._max_record_history:
            removable = next(
                (
                    task_id
                    for task_id, record in self._records.items()
                    if record.state in _TERMINAL_STATES
                ),
                None,
            )
            if removable is None:
                return
            removed = self._records.pop(removable)
            if removed.idempotency_key is not None:
                self._idempotency.pop(removed.idempotency_key, None)

    @staticmethod
    def _transition(
        record: _TaskRecord,
        state: TaskState,
        *,
        worker_name: str | None = None,
        error_code: str | None = None,
    ) -> None:
        if record.state in _TERMINAL_STATES:
            return
        now = _now()
        record.state = state
        record.updated_at = now
        if worker_name is not None:
            record.assigned_worker = worker_name
        if error_code is not None:
            record.error_code = error_code
        record.events.append(
            LifecycleEvent(
                state=state,
                occurred_at=now,
                worker_name=worker_name,
                error_code=error_code,
            )
        )
        if state in _TERMINAL_STATES:
            record.completed.set()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _snapshot(record: _TaskRecord) -> TaskSnapshot:
    return TaskSnapshot(
        task_id=record.task.task_id,
        state=record.state,
        created_at=record.created_at,
        updated_at=record.updated_at,
        assigned_worker=record.assigned_worker,
        result=record.result,
        error_code=record.error_code,
        events=tuple(record.events),
    )
