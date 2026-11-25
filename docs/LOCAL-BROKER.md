# Local Broker — Stage 1

**Status:** first local-only implementation under review in [PR #15](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/15).

The broker is a bounded in-process dispatcher for agents explicitly registered by the local operator. It is not a network service, federation layer, durable queue, or authorization system.

## Current behavior

- Non-blocking admission returns `accepted`, `deferred`, or `rejected`.
- Queue and in-memory task history have configured bounds (defaults: 128 queued tasks and 256 retained records).
- UTF-8 prompt and result sizes are bounded (defaults: 64 KiB per prompt and 128 KiB per result); oversize input is rejected and oversize output is not retained.
- Workers declare capabilities; a task is routed only to a registered worker satisfying every requested capability.
- Worker concurrency and shared per-node concurrency are bounded.
- Idempotency keys prevent duplicate execution while their task record remains in the bounded history.
- Tasks have explicit admission acknowledgements and lifecycle events.
- Deadlines expire work; callers can cancel queued or running tasks.
- Snapshots expose state, timestamps, worker attribution, result, stable error code, and lifecycle events. Prompts are not included in snapshots or event metadata.
- Worker exception details are withheld; the broker records a stable error code instead.

## Minimal example

```python
import asyncio

from tushka import LocalBroker, Task, WorkerRegistration
from tushka.core import AgentResult


class SummaryAgent:
    name = "local-summary"

    async def run(self, task: Task) -> AgentResult:
        return AgentResult(self.name, f"Received {len(task.prompt)} characters")


async def main() -> None:
    worker = SummaryAgent()
    broker = LocalBroker(
        [
            WorkerRegistration(
                agent=worker,
                capabilities=frozenset({"summarize"}),
                node_id="this-process",
                max_concurrency=1,
            )
        ],
        max_queued_tasks=32,
        max_record_history=256,
        max_prompt_bytes=65_536,
        max_result_bytes=131_072,
        per_node_concurrency=1,
    )
    await broker.start()
    try:
        admission = broker.submit(
            Task("task-001", "Summarize this local input"),
            required_capabilities=("summarize",),
            idempotency_key="request-001",
        )
        if admission.status.value == "accepted":
            result = await broker.wait(admission.task_id)
            print(result.state.value, result.assigned_worker)
    finally:
        await broker.close()


asyncio.run(main())
```

## Admission outcomes

| Outcome | Meaning | Caller action |
|---|---|---|
| `accepted` | The task was recorded and placed in a local worker queue | Track the returned task ID |
| `deferred` | Queue or bounded record history is at capacity | Retry after `retry_after_seconds` with the same idempotency key |
| `rejected` | The broker is not running, no worker has the required capabilities, or the request is invalid | Correct the request or configuration |

A repeated idempotency key with the same request returns the original task ID. Reusing a key for a different task is rejected as a conflict.

## Lifecycle

`created → accepted → queued → assigned → running → succeeded | failed | cancelled | expired`

Lifecycle events record state, UTC timestamp, optional worker name, and stable error code. They do not contain prompts or raw exception text.

## Safety and limitations

- Start with explicitly registered local workers only.
- A capability label is routing metadata, not permission to access a file, secret, conversation, or private memory.
- This implementation does not synchronize memory or dispatch work to remote nodes.
- There is no persistent storage; process shutdown loses queued work and in-memory history.
- Retries, exponential backoff, dead-letter review, fairness guarantees, transport authentication, cross-node authorization, and durable recovery are not implemented in this slice.
- Idempotency is bounded by the configured in-memory record-history window; it is not a durable exactly-once guarantee.
- The broker does not provide a production security boundary. Do not pass secrets or private data to a worker unless the local operator has independently authorized that worker and its execution environment.

See [Issue #6](https://github.com/TushkaLoLz31337/tushka-swarm-collective/issues/6) for the full implementation sequence and remaining acceptance criteria.
