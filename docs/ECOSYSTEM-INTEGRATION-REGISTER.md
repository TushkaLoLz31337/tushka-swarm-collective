# Tushka Ecosystem Integration Register

**Review date:** 2026-11-24  
**Purpose:** Record potentially reusable projects without obscuring authorship, license, source history, or implementation status.

This register distinguishes **reference**, **candidate**, and **integrated**. A link to a project is not an endorsement or a claim that its code is part of Tushka. No code from the projects below was copied into Tushka as part of this register.

## First-party ecosystem candidates

| Project / source repository | Repository owner / authorship record | License observed | Relevant capability | Tushka disposition |
|---|---|---|---|---|
| [OpenWorkSpace](https://github.com/HuffmanMainNode/OpenWorkSpace) | GitHub repository owned by `HuffmanMainNode`; retain source copyright notices and any NOTICE file | Apache-2.0 | Local capability registry, identity metadata, task lifecycle store, local SQLite message queue, permission-decision helper, hash-linked evidence journal, resource catalog | **Candidate.** Strong overlap with local workspace, registry, and evidence needs. Its README explicitly says identity is not remote authentication, permissions are not OS enforcement, queue is local-only, and arbitrary plugin execution is disabled. |
| [Open Intelligence Exchange (OIX)](https://github.com/HuffmanMainNode/Open-Intelligence-Exchange) | GitHub repository owned by `HuffmanMainNode`; LICENSE copyright: “Open Intelligence Exchange contributors” (2026) | MIT | Signed agent cards/messages, key lifecycle, encrypted envelope option, receipts, replay controls, authorization queue, experimental mutual-TLS transport and peer exchange | **Candidate.** Best fit for exchange envelope and node-to-node interoperability. Transport and cryptographic operations require independent security review; README documents key-custody and maturity limits. |
| [Open-Swarm](https://github.com/HuffmanMainNode/-Open-Swarm) | GitHub repository owned by `HuffmanMainNode`; LICENSE copyright: “Open-Swarm contributors” (2026) | MIT | Durable SQLite task queue, leases/retries, worker capability registry, local model adapters, approval gates, audit journal, optional OIX handoff adapter | **Candidate.** Strong broker/worker reference and possible adapter target. README describes an initial implementation and explicitly says it is not a production security boundary. |
| [Mesh Archivist Engine fork](https://github.com/Ryzean84/mesh-archivist-engine-ControlledFork-by-MrCakes931-) | Repository owned by `Ryzean84`; confirmed fork of `HuffmanMainNode/mesh-archivist-engine`. Fork `main` and upstream `main` compared identical at commit `9fd47d6cf0f4791254a9745b246b5a2223f1779e`. Recent commit author is `MrCakes931`; do not attribute those files to the fork owner solely from ownership. | Apache-2.0 | Local checkpoints, resume/verify workflow, hash-chained WAL, explicit execution approval, scoped agent handshake | **Reference only; lineage confirmed.** Useful recovery and handoff patterns; no code copied. Fork has no distinct delta from upstream at the pinned checkpoint. |
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


## Source-pinned technical evaluation — 2026-11-24

The following observations were checked against the exact commits below. They are repository-level observations, not production security endorsements.

| Candidate | Evaluated source commit | Relevant implementation evidence | Tushka comparison and disposition |
|---|---|---|---|
| Open-Swarm | `HuffmanMainNode/-Open-Swarm@bf94be4faf8f9de00a5248b389caf06b6b1577cc` | SQLite task queue; bounded admission (default 500 queued); transactional claim with `BEGIN IMMEDIATE`; per-claim UUID lease; lease expiry requeues or fails at max attempts; configurable retry count; explicit approval state; structured audit and transactional integration outbox. Policy caps prompt/output characters, allowlists adapters, checks capability labels, and gates approval-required tasks. | **Strong local broker reference / adapter candidate.** Tushka PR #15 currently provides an in-memory bounded queue, capability routing, concurrency limits, idempotency, deadlines, cancellation, lifecycle events, and byte-bounded payload/history. It does not yet provide durable claims, leases, retries, approval workflow, persistent audit, or outbox. Next Tushka broker slice should define lease/attempt semantics and a store interface before selecting SQLite or copying any implementation. Open-Swarm stores prompts/results/errors/audit details in plaintext; file modes are not encryption or multi-tenant isolation. |
| OIX | `HuffmanMainNode/Open-Intelligence-Exchange@8062c55588cd4e811fd3bda280fde5866a4f469a` | Signed envelope with Ed25519 identity/signature, UUID message ID, sender/recipient, message type, issued/expiry times, nonce, requested capability, and object payload. Restricted canonical JSON rejects floats and non-string keys. Inbox verifies trusted peers, replay controls, capability allowlists, and approval-gated durable inbound work; it persists data and does not execute payloads. Optional encrypted envelopes and mutual-TLS transport are experimental. | **Exchange adapter candidate, not dependency.** Tushka task/result payloads can be nested in OIX `task.request`/`task.result` payloads while keeping OIX message ID distinct from Tushka task ID. A shape-level compatibility fixture and nested Tushka schema tests are ready in [PR #16](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/16); Ruff lint/format, unit tests, and demo smoke test passed. It does not claim signature verification. OIX documents unencrypted local private-key storage, no global revocation service, and capability labels that do not enforce downstream OS permissions. Keep network transport disabled until identity, key custody, authorization, replay, quotas, and threat-model review are complete. |
| OpenWorkSpace | `HuffmanMainNode/OpenWorkSpace@0c7c4239f69fcba901b22a37adcb13de97f4c3ac` | Local capability registry, identity metadata lifecycle, task lifecycle store, SQLite message queue, permission-decision helper, hash-linked evidence journal, resource catalog. README states identity records do not authenticate principals, permission helper is not OS enforcement, local queue has no sender authentication, and task records do not execute themselves. | **Metadata/evidence reference.** Potentially useful for a future registry/evidence adapter; do not use its permission helper as authorization or duplicate its storage without an explicit boundary and measured need. No code copied. |
| Mesh Archivist Engine | Fork and upstream `main@9fd47d6cf0f4791254a9745b246b5a2223f1779e` | Hash-chained WAL with fsync and file locking, explicit recovery/verification, plan-only resume, dry-run summon by default, explicit `--execute`, scoped agent handshake, and host-provided approval verifier requirement for side effects. Fork metadata identifies parent `HuffmanMainNode/mesh-archivist-engine`; GitHub compare reports fork and upstream main identical at the checkpoint. | **Recovery/handoff reference only.** Lineage is confirmed; the fork contains no distinct commit delta at the pinned checkpoint. Commit author records show `MrCakes931`, while repository owner is `Ryzean84`; retain that distinction. No code copied. |

### Interoperability guardrails

- Tushka's task/result schemas remain authoritative for Tushka payload semantics; an outer OIX envelope supplies sender/recipient identity, message ID, expiry, nonce, requested capability, and signature.
- Envelope signature validity does not authorize execution. A receiving Tushka broker must still apply its own capability policy, approval state, payload limits, and local operator authorization.
- Do not persist OIX private keys in Tushka task records, logs, prompts, or artifacts.
- Do not treat OpenWorkSpace identity metadata, permission decisions, or Mesh approval references as independently authenticated unless the host verifies the underlying cryptographic proof.
- Any future code reuse requires exact file-level attribution, upstream notices, license compatibility review, and independent security review.
