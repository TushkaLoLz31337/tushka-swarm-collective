"""Minimal asynchronous coordinator for independent task agents.

This module deliberately knows nothing about a particular model provider.
Adapters implement the Agent protocol and can call local or hosted systems.
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Task:
    """A unit of work sent to participating agents."""

    task_id: str
    prompt: str

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be a non-empty string.")
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("prompt must be a non-empty string.")


@dataclass(frozen=True, slots=True)
class AgentResult:
    """An attributable result returned by one agent."""

    agent_name: str
    content: str
    success: bool = True
    error: str | None = None


class Agent(Protocol):
    """Interface implemented by every model, tool, or human-backed agent."""

    name: str

    async def run(self, task: Task) -> AgentResult:
        """Execute a task and return an attributable result."""
        ...


class Coordinator:
    """Dispatch tasks concurrently and combine successful agent responses."""

    def __init__(self, agents: Sequence[Agent], timeout_seconds: float = 60.0):
        if not agents:
            raise ValueError("Coordinator requires at least one agent.")
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a finite positive number.")

        names = [agent.name for agent in agents]
        if any(not isinstance(name, str) or not name.strip() for name in names):
            raise ValueError("Every agent must have a non-empty name.")
        if len(set(names)) != len(names):
            raise ValueError("Agent names must be unique within a coordinator.")

        self.agents = tuple(agents)
        self.timeout_seconds = timeout_seconds

    async def run(self, task: Task) -> list[AgentResult]:
        """Run all agents concurrently, isolating individual failures."""
        if not isinstance(task, Task):
            raise TypeError("task must be a Task instance.")

        async def invoke(agent: Agent) -> AgentResult:
            try:
                result = await asyncio.wait_for(
                    agent.run(task), timeout=self.timeout_seconds
                )
                if not isinstance(result, AgentResult):
                    return AgentResult(
                        agent_name=agent.name,
                        content="",
                        success=False,
                        error="Agent returned an invalid result type.",
                    )
                if result.agent_name != agent.name:
                    return AgentResult(
                        agent_name=agent.name,
                        content="",
                        success=False,
                        error="Agent identity mismatch in returned result.",
                    )
                return result
            except TimeoutError:
                return AgentResult(
                    agent_name=agent.name,
                    content="",
                    success=False,
                    error=f"Timed out after {self.timeout_seconds:g} seconds.",
                )
            except Exception as exc:  # noqa: BLE001 - isolate arbitrary agent failures without leaking details
                return AgentResult(
                    agent_name=agent.name,
                    content="",
                    success=False,
                    error=f"{type(exc).__name__}: agent execution failed; details withheld.",
                )

        return list(await asyncio.gather(*(invoke(agent) for agent in self.agents)))

    @staticmethod
    def synthesize(results: Sequence[AgentResult]) -> str:
        """Create a transparent first-pass synthesis without hiding attribution."""
        usable = [r for r in results if r.success and r.content.strip()]
        if not usable:
            failures = "; ".join(
                f"{r.agent_name}: {r.error or 'empty response'}" for r in results
            )
            raise RuntimeError(f"No usable agent results. {failures}")

        sections = ["# Combined agent results"]
        for result in usable:
            sections.append(f"## {result.agent_name}\n{result.content.strip()}")

        failed = [r for r in results if not r.success]
        if failed:
            sections.append("## Agent failures")
            sections.extend(
                f"- {r.agent_name}: {r.error or 'unsuccessful'}" for r in failed
            )
        return "\n\n".join(sections)
