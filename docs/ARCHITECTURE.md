# Tushka architecture

## Current implementation boundary

The current alpha has a local asynchronous coordinator. It dispatches one task to multiple independent agents, collects attributable results, isolates individual failures, applies a timeout, and produces a transparent first-pass result collection.

The deterministic demo agents are stand-ins. The first local model adapter implements the same Agent interface through an explicitly configured Ollama-compatible chat endpoint. The coordinator remains provider-neutral.

## Target architecture

    User / Application
            |
      Task Coordinator
            |
      Task routing and policy
        /      |      \
    Agent A  Agent B  Agent C
       |        |        |
    Adapter  Adapter  Adapter
       |        |        |
    Local model / open model / optional hosted model

    Knowledge domains (introduced incrementally):
    - private local memory, controlled by each node owner
    - shared community commons, populated only by explicit opt-in
    - verified knowledge views with provenance, status, and revision history

    Shared services (introduced incrementally):
    - provenance-aware retrieval and export/import
    - evaluation and verification
    - permissions, identity, and audit events
    - authenticated federated synchronization and node transport

## Core boundaries

- **Coordinator:** task lifecycle, dispatch, timeout, result collection.
- **Agent:** a capability with a stable identity and a narrow execution interface.
- **Adapter:** translates the agent interface to a model, tool, or external runtime.
- **Knowledge service:** stores sourced, versioned material; it must not silently overwrite source history.
- **Evaluation:** checks outputs against task-specific criteria and independent evidence.
- **Node runtime:** later enables remote execution with explicit trust and resource policies.

## Design constraints

1. The core must not import a vendor SDK.
2. Provider credentials belong in local secret stores or environment configuration, never source control.
3. Every result must retain agent identity and success/failure status.
4. Partial failure must not erase successful results from other agents.
5. Private local memory is never synchronized by default; sharing requires explicit owner action.
6. Networked nodes are untrusted by default; authentication, authorization, isolation, and resource limits are required before remote execution.
7. Model output is data, not trusted instructions.
8. Knowledge entries must preserve source, author, license, timestamp, and revision history where applicable.

## Next interfaces

Before adding networking, define stable contracts for:
- task identifiers, deadlines, cancellation, and task status;
- agent capabilities and resource declarations;
- structured result metadata and provenance;
- evaluation verdicts and confidence/uncertainty;
- adapter configuration and secret handling.

Avoid prematurely choosing a single message broker, vector database, model provider, or orchestration framework.


## Companion project interoperability

The target architecture is documented in [Autonomous Swarm Specification v1](AUTONOMOUS-SWARM-SPECIFICATION-v1.md). Tushka will evaluate existing local-first components through adapters rather than duplicate their functionality. See the [Ecosystem Integration Register](ECOSYSTEM-INTEGRATION-REGISTER.md) for source ownership, licenses, maturity boundaries, and the distinction between reference, candidate, and integrated projects. No companion project is part of the Tushka runtime merely because it is listed there.
