# Interoperability Boundaries and OIX Contract Fixture

**Status:** shape-level interoperability test proposed in [PR #16](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/16). No OIX runtime dependency, transport, or cryptographic implementation is added.

## Source pins

- Tushka task/result contracts: this repository's `spec/v1/task.schema.json` and `spec/v1/result.schema.json`.
- OIX message envelope reference: [HuffmanMainNode/Open-Intelligence-Exchange](https://github.com/HuffmanMainNode/Open-Intelligence-Exchange), evaluated at commit `8062c55588cd4e811fd3bda280fde5866a4f469a`, MIT, copyright Open Intelligence Exchange contributors.
- OIX message schema: `protocol/schemas/message.schema.json` at that pinned commit. The compatibility test deliberately does not copy this third-party schema; it checks the documented envelope fields and validates the nested payload against Tushka's own versioned schemas.

## Field mapping

| OIX v0.1 envelope | Tushka payload / meaning | Boundary |
|---|---|---|
| `body.message_id` | Distinct OIX transport message ID | Must not be substituted for Tushka `task_id` |
| `body.sender`, `body.recipient` | OIX agent identity references | Must be verified by OIX identity/trust code before the broker receives work |
| `body.issued_at`, `body.expires_at`, `body.nonce` | Freshness and replay metadata | Validate before dispatch; not task lifecycle state |
| `body.requested_capability` | Tushka required capability label | Routing metadata only; broker and local policy still decide eligibility |
| `body.type = task.request` | `body.payload` validates as Tushka task schema | Preserve `protocol_version`, `message_type`, `task_id`, and `prompt` exactly |
| `body.type = task.result` | `body.payload` validates as Tushka result schema | Preserve Tushka `task_id`, `agent_id`, `status`, and result/error shape |
| Outer `signature` | OIX signature over canonical envelope body | Must be verified by OIX; the fixture signature is intentionally a placeholder |

## What the test proves

The test fixtures demonstrate that a Tushka v1 task and result can be carried inside the OIX v0.1 `task.request` and `task.result` payload slots without adding fields to, or changing, the Tushka schemas. It checks the envelope's required field set, message type, identifier separation, timestamps, nonce/capability shape, and nested Tushka schema validation.

The test does **not** prove:
- a valid Ed25519 signature or trusted sender;
- OIX canonical JSON/signature verification;
- replay-cache behavior or expiry enforcement;
- capability authorization or human approval;
- transport authentication, confidentiality, or remote execution.

The placeholder signature is not a valid signature and must never be used in a live exchange.

## Security and deployment decision

OIX remains an **adapter candidate**, not a Tushka runtime dependency. Its source documents experimental mutual-TLS transport, local plaintext private-key storage, no global revocation service, and the distinction between capability labels and downstream OS enforcement.

A future OIX adapter must perform, in order:

1. Verify the envelope shape, canonical encoding, sender key, and signature.
2. Check explicit trusted-peer enrollment, message expiry, and durable replay state.
3. Apply the local capability allow-list and approval policy.
4. Validate the nested Tushka task schema and enforce prompt/result byte limits.
5. Submit only to an explicitly configured local broker worker.
6. Return a Tushka result in a new signed OIX `task.result` envelope after policy approval.

A valid signature is not execution authorization. No remote dispatch or private-memory synchronization is enabled by this document or the fixtures.

## Companion project decisions

- **Open-Swarm** (`HuffmanMainNode/-Open-Swarm@bf94be4faf8f9de00a5248b389caf06b6b1577cc`, MIT): durable SQLite queue, leases, retry limits, approval gate, audit events, and transactional outbox are strong local broker references. Its prompts/results/audit are stored in plaintext and its capability labels are not OS-level grants. Tushka's first broker PR is in-memory; a future store interface and lease model should be evaluated before choosing persistence.
- **OpenWorkSpace** (`HuffmanMainNode/OpenWorkSpace@0c7c4239f69fcba901b22a37adcb13de97f4c3ac`, Apache-2.0): useful local registry and evidence-journal reference. Its own documentation says identity metadata is not authentication, permission helper is not OS enforcement, and its local queue has no sender authentication.
- **Mesh Archivist Engine** (`Ryzean84/mesh-archivist-engine-ControlledFork-by-MrCakes931-@9fd47d6cf0f4791254a9745b246b5a2223f1779e`, Apache-2.0): fork lineage is confirmed against `HuffmanMainNode/mesh-archivist-engine`; fork and upstream `main` compared identical at the pinned commit. Its WAL recovery, plan-only resume, dry-run default, and host-verified approval boundary are reference patterns. The observed repository owner is `Ryzean84`; recent commit author is `MrCakes931`. Do not conflate repository ownership with per-file authorship.

No companion code has been copied or integrated. Preserve original license and author records if future reuse is proposed.
