# Tushka Swarm Collective

**An open, model-independent collective of cooperating AI agents and community-operated nodes.**

Tushka is an effort to build practical, inspectable, and extensible swarm intelligence without locking the system to one model vendor, account, machine, or coordinator.

## What we're building

- **Agent collaboration:** independent agents receive a task, work in parallel, and return attributable results.
- **Model independence:** adapters can connect local models, open models, and optional hosted providers.
- **Local-first operation:** core orchestration should run on an ordinary developer machine.
- **Shared knowledge with provenance:** contributions remain attributable, sourced, versioned, and reviewable.
- **Federated participation:** people can operate nodes and contribute capabilities without surrendering ownership of their own projects.
- **Verifiable behavior:** tests, evaluations, logs, and explicit failure states are part of the system.
- **Purposeful continuity:** records have stable identities, explicit purposes, directional lifecycle paths, bounded retention, and correction/deletion workflows.
- **Compliance by design:** each use case must pass privacy, security, platform-terms, licensing, and jurisdiction-specific review before release or activation.

## First working milestone

The initial prototype is intentionally small:

1. A coordinator accepts a task.
2. It dispatches the task to independent agents.
3. It collects attributable results.
4. It reports usable results and explicit failures.
5. It produces a transparent first-pass result collection.

The deterministic demo agents remain placeholders, not claims of autonomous intelligence. The first real local-model adapter is available through the existing agent interface. It uses an explicitly configured Ollama-compatible chat endpoint and Python's standard library. See [Local Model Adapter](docs/LOCAL-MODEL-ADAPTER.md).

## Quick start

Requires Python 3.11 or newer. From the repository root:

    python -m pip install -e .
    python -m unittest discover -s tests -v
    python -m tushka.demo

## Repository map

- src/tushka/ — coordinator, agent interface, local adapter, and runnable demo
- tests/ — automated tests for core behavior and local HTTP adapter behavior
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system boundaries and design principles
- [docs/LOCAL-MODEL-ADAPTER.md](docs/LOCAL-MODEL-ADAPTER.md) — local inference configuration and limits
- [docs/ROADMAP.md](docs/ROADMAP.md) — staged implementation plan
- [docs/WORKING-CHECKPOINT.md](docs/WORKING-CHECKPOINT.md) — shared status, handoffs, and resume instructions
- [docs/AUTONOMOUS-SWARM-SPECIFICATION-v1.md](docs/AUTONOMOUS-SWARM-SPECIFICATION-v1.md) — target subsystem boundaries and agent handoff contract
- [docs/ECOSYSTEM-INTEGRATION-REGISTER.md](docs/ECOSYSTEM-INTEGRATION-REGISTER.md) — companion projects, licenses, authorship, and integration status
- [docs/RECORD-GOVERNANCE.md](docs/RECORD-GOVERNANCE.md) — immutable provenance, identifiers, tags, directional paths, retention, and storage-bloat controls (proposed)
- [docs/COMPLIANCE-AND-USE-POLICY.md](docs/COMPLIANCE-AND-USE-POLICY.md) — project-wide legal, privacy, security, platform, and license guardrails (proposed)
- [docs/USE-CASE-REGISTER.md](docs/USE-CASE-REGISTER.md) — mandatory per-use-case assessment template and initial register
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to participate
- [SECURITY.md](SECURITY.md) — responsible security reporting

## Design principles

1. No single model, provider, account, machine, or maintainer is indispensable.
2. No silent rewriting of contributed knowledge or project history.
3. Preserve authorship, licenses, source links, and upstream relationships.
4. Prefer small interoperable modules over a monolith.
5. Treat model output as untrusted until evaluated.
6. Make failures, uncertainty, and provenance visible.
7. Keep the core runnable without a proprietary API dependency.
8. Collect only what is necessary, for a declared purpose, and retain it only as long as justified.
9. Private data is private by default; sharing and external side effects require scoped authorization.
10. Every use case must be assessed before it is enabled; no prototype, local node, or agent is exempt.

## Project status

**Stage 1 alpha (v0.1.0-alpha) — experimental.** The coordinator, deterministic demo, and first local-model adapter establish an executable agent integration seam. Distributed networking, persistent memory, immutable record storage, federation, and production security are not implemented. Governance documents linked above are proposed contracts pending review and implementation. See [Stage 1 release notes](docs/RELEASE-0.1.0-alpha.md).

## License

Licensed under the [Apache License 2.0](LICENSE).

## Mission, goals, and roadmap

Read the [North Star and strategic goals](docs/GOALS-AND-NORTH-STAR.md), the [living roadmap](docs/ROADMAP.md), and the [contribution review process](docs/CONTRIBUTION-REVIEW-PROCESS.md).

## Knowledge ownership

Tushka's target design distinguishes private local memory, the opt-in shared community commons, and verified knowledge views. These are future architecture goals, not features of the current alpha. See [Knowledge Architecture](docs/KNOWLEDGE-ARCHITECTURE.md).

## Community

Tushka welcomes people at every experience level. See [Contributing](CONTRIBUTING.md) to find a starting point, and consult the [shared working checkpoint](docs/WORKING-CHECKPOINT.md) for current work, handoffs, and resume instructions. The public ecosystem front door and upstream contribution workflow are maintained separately at [TushkaLoLz31337](https://github.com/TushkaLoLz31337/TushkaLoLz31337).
