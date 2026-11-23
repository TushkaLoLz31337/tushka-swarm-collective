# Tushka Ecosystem Integration Register

**Review date:** 2026-11-23  
**Purpose:** Record potentially reusable projects without obscuring authorship, license, source history, or implementation status.

This register distinguishes **reference**, **candidate**, and **integrated**. A link to a project is not an endorsement or a claim that its code is part of Tushka. No code from the projects below was copied into Tushka as part of this register.

## First-party ecosystem candidates

| Project / source repository | Repository owner / authorship record | License observed | Relevant capability | Tushka disposition |
|---|---|---|---|---|
| [OpenWorkSpace](https://github.com/HuffmanMainNode/OpenWorkSpace) | GitHub repository owned by `HuffmanMainNode`; retain source copyright notices and any NOTICE file | Apache-2.0 | Local capability registry, identity metadata, task lifecycle store, local SQLite message queue, permission-decision helper, hash-linked evidence journal, resource catalog | **Candidate.** Strong overlap with local workspace, registry, and evidence needs. Its README explicitly says identity is not remote authentication, permissions are not OS enforcement, queue is local-only, and arbitrary plugin execution is disabled. |
| [Open Intelligence Exchange (OIX)](https://github.com/HuffmanMainNode/Open-Intelligence-Exchange) | GitHub repository owned by `HuffmanMainNode`; LICENSE copyright: “Open Intelligence Exchange contributors” (2026) | MIT | Signed agent cards/messages, key lifecycle, encrypted envelope option, receipts, replay controls, authorization queue, experimental mutual-TLS transport and peer exchange | **Candidate.** Best fit for exchange envelope and node-to-node interoperability. Transport and cryptographic operations require independent security review; README documents key-custody and maturity limits. |
| [Open-Swarm](https://github.com/HuffmanMainNode/-Open-Swarm) | GitHub repository owned by `HuffmanMainNode`; LICENSE copyright: “Open-Swarm contributors” (2026) | MIT | Durable SQLite task queue, leases/retries, worker capability registry, local model adapters, approval gates, audit journal, optional OIX handoff adapter | **Candidate.** Strong broker/worker reference and possible adapter target. README describes an initial implementation and explicitly says it is not a production security boundary. |
| [Mesh Archivist Engine fork](https://github.com/Ryzean84/mesh-archivist-engine-ControlledFork-by-MrCakes931-) | Repository owned by `Ryzean84`; repository name identifies it as a controlled fork. Original upstream lineage and per-file authorship must be confirmed before code reuse. | Apache-2.0 observed in fork LICENSE | Local checkpoints, resume/verify workflow, hash-chained WAL, explicit execution approval, scoped agent handshake | **Reference only pending lineage review.** Useful recovery and handoff patterns; no code copied. Confirm upstream origin, commit ancestry, notices, and compatibility before any adoption. |
| [Ryzean84 Tushka fork](https://github.com/Ryzean84/tushka-swarm-collective-ForkByRyzean84) | Fork owned by `Ryzean84`; upstream is Tushka Swarm Collective | Inherited project license; verify fork history before attributing new work | Independent fork/upstream workspace | **Collaboration workspace.** No distinct implementation was identified in the README review; upstream changes only through reviewed PRs. |

## External open-source reference

| Project | Authorship | License observed | Relevance | Disposition |
|---|---|---|---|---|
| [OpenAI Swarm](https://github.com/openai/swarm) | Published by the `openai` GitHub organization / OpenAI Solutions team | MIT (repository metadata) | Educational examples of lightweight multi-agent handoffs and routines | **Reference only.** No code copied and no runtime dependency selected. |

## Attribution and reuse rules

1. Preserve the original repository URL, owner, copyright notices, LICENSE, and NOTICE content when applicable.
2. For Apache-2.0 reuse, include the license, retain applicable notices, mark modified files, and carry forward applicable NOTICE attributions.
3. For MIT reuse, retain the copyright and permission notice in copies or substantial portions.
4. Do not infer an individual author from a repository owner. Use commit authorship and the source repository's notices when attributing specific files.
5. For forks, identify both the fork location and upstream origin; do not erase upstream history or present inherited work as newly authored.
6. Keep copied, adapted, linked, and independently reimplemented components distinct in the register and in code comments/docs.
7. Before adding a dependency or vendoring code, review the exact commit, license compatibility, security posture, dependencies, tests, and maintainer activity.
8. Public availability is not permission to ignore licenses, privacy, or unpublished contributor material.

## Status vocabulary

- **Reference only:** useful design or research pointer; no code or runtime dependency.
- **Candidate:** selected for technical, license, and security evaluation; not integrated.
- **Integrated:** adapter or code is merged into Tushka and verified with tests. Record the exact commit, source version, author attribution, and changes here.
- **Rejected / deferred:** not selected; record the reason and revisit trigger.

## Review queue

- [ ] Compare Open-Swarm task lifecycle and queue semantics against Tushka Issue #6 acceptance criteria.
- [ ] Build contract fixtures to test Tushka task/result envelopes through an OIX message wrapper without semantic drift.
- [ ] Review OpenWorkSpace storage and evidence interfaces for a small adapter boundary; do not duplicate its database or claim its controls are enforcement.
- [ ] Confirm Mesh Archivist Engine upstream repository and commit ancestry before code-level reuse.
- [ ] Record exact source commits and test evidence before changing any entry to **Integrated**.
