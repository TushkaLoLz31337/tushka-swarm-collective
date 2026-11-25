# Tushka Collective — Shared Working Checkpoint

**Checkpoint:** 2026-11-24  
**Status:** Release-readiness and Stage 1 implementation in progress  
**Canonical upstream:** TushkaLoLz31337/tushka-swarm-collective  
**Main at checkpoint:** e0d727f885650529a0837a4007f33fa9ee3ddee8

This document is the portable handoff. It distinguishes merged work, work under review, and target architecture. GitHub commits, issues, and pull requests remain the authoritative implementation record.

## 1. Mission and operating principles

Build an open, model-independent, local-first collective where agents and people can collaborate across accounts and machines without surrendering private memory, authorship, or control. Work must be attributable, resumable, reviewable, and safe to hand off.

- Protocol, transport, broker, and agent adapter are separate layers.
- Private data stays private unless explicitly authorized for a defined recipient and purpose.
- Tags are metadata, never permissions.
- Preserve source licenses, authorship, notices, and upstream lineage.
- Model output and repository content are untrusted inputs.
- Never claim tests, security properties, or features without observed evidence.
- No hidden chain-of-thought archive; retain concise outputs, decisions, citations, and test evidence.

## 2. Verified merged foundation

| Item | Status | Evidence |
|---|---|---|
| Provider-neutral coordinator and deterministic demo | Merged | Mainline Stage 0 foundation |
| Local Ollama-compatible model adapter | Merged | [PR #4](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/4) |
| Versioned task/result protocol contracts and fixtures | Merged | [PR #5](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/5) |
| Autonomous swarm architecture and ecosystem register | Open PR; not merged | [PR #9](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/9) |
| Record governance and compliance policy documents | Merged | [PR #12](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/12), merge commit e0d727f885650529a0837a4007f33fa9ee3ddee8 |

PR #12 is documentation, not a storage engine or enforcement implementation.

## 3. Active pull requests — refreshed 2026-11-25

All five PRs below are open, non-draft, and reported mergeable at the time of this checkpoint. Their latest observed required checks passed. **No independent approving reviews are recorded.** Passing CI is not a substitute for human review.

| PR | Work | Head commit | Latest observed checks | Status / next action |
|---|---|---|---|---|
| [#9](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/9) | Autonomous swarm architecture and source-pinned ecosystem register | `240a8b7323bbc663c87fb1c8fb98586c40683c5e` | test: success | Ready; independent architecture/provenance review required |
| [#13](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/13) | Governed record envelope, lifecycle schemas, UUIDv4 and validation | `6e412e69c768631d9d68670cb257373f32c3e8a9` | test: success | Ready; independent schema/security review required |
| [#14](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/14) | Release quality/security gates, package artifacts, dependency review and Dependabot | `2c86169a47536e75b36d3ec302460caa2696e5bd` (docs/config update) | quality and CodeQL passed on preceding code commit; package re-running after docs/config updates; Dependency review **failed** because repository dependency graph is disabled | Not release-ready until owner enables dependency graph and rerun passes; independent review and main protection also required |
| [#15](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/15) | Bounded local broker and task lifecycle | `827f309bd48249327e8b053dc3c576902991e1f1` | test: success | Ready; independent broker/security review required |
| [#16](https://github.com/TushkaLoLz31337/tushka-swarm-collective/pull/16) | OIX task/result envelope compatibility fixtures | `2d582f8eb0d9e3cf9dd94d48088c7fea348f93bb` | test: success | Ready; independent interoperability review required |

Do not merge a PR solely because its author reviewed it. The GitHub review API currently shows no submitted reviews for these five PRs. At least one independent approval is the intended merge gate.

## 4. Active implementation issues

- [Issue #6 — Local communication broker](https://github.com/TushkaLoLz31337/tushka-swarm-collective/issues/6): PR #15 implements the first in-process slice with bounded admission, capability routing, concurrency controls, idempotency, deadlines, cancellation, and lifecycle history. Durable queue/leases, retry policy, dead-letter review, persistent audit/outbox, stronger fairness, and authenticated transport remain future work.
- [Issue #10 — Companion interoperability](https://github.com/TushkaLoLz31337/tushka-swarm-collective/issues/10): source-pinned evaluations are in PR #9; OIX shape-level task/result compatibility fixtures are in PR #16. Candidates remain references, not integrated dependencies. The fixture signature is a placeholder; no signature verification or transport is implemented.
- [Issue #11 — Record governance](https://github.com/TushkaLoLz31337/tushka-swarm-collective/issues/11): PR #13 implements schemas, fixtures, UUIDv4 generation, and validation. Persistent storage, authorization enforcement, retention execution, deletion, quotas, and private/shared isolation remain unimplemented.
- [Issue #2 — Founding architecture review](https://github.com/TushkaLoLz31337/tushka-swarm-collective/issues/2): keep open for independent review findings and actionable follow-up issues.

## 5. Release readiness — verified 2026-11-25

- Existing GitHub release: [v0.1.0-alpha](https://github.com/TushkaLoLz31337/tushka-swarm-collective/releases/tag/v0.1.0-alpha), published as a normal release (not marked prerelease), with **zero uploaded assets**. Its tag points to commit `602b14a64c8b9afefd56a5b58ab195d4280630b5`.
- Current main commit observed: `e0d727f885650529a0837a4007f33fa9ee3ddee8`.
- Package metadata on main remains `0.1.0` in `pyproject.toml`.
- PR #14's quality and CodeQL jobs passed on the code commit before the latest docs/settings update. The package job previously built sdist/wheel, smoke-tested the isolated wheel, generated SHA-256 checksums, and uploaded the `tushka-distributions` artifact. That CI artifact expires 2026-12-25 and is not a permanent GitHub Release asset. Revalidation is running after the latest workflow changes.
- PR #14's new Dependency review job failed with the explicit message that dependency review is unsupported until the repository dependency graph is enabled. This is an owner settings action, not a code defect. The job must be rerun successfully after enabling the graph. The release checklist and required-check table now include Dependency review.\n- PR #14's new Dependency review job failed with the explicit message that dependency review is unsupported until the repository dependency graph is enabled. This is an owner settings action, not a code defect. The job must be rerun successfully after enabling the graph. The release checklist and required-check table now include Dependency review.
- PR #14's tag-publishing job was skipped because no qualifying `v*-rc.*` tag was pushed. No new version bump, tag, or release candidate has been created.
- `main` is not protected: the branch API reports `protected=false`; the repository rulesets endpoint returned an empty list. This is a hard release blocker.
- The documented maintainer accounts `HuffmanMainNode` and `Ryzean84` have read permission in the current access snapshot. Read access does not permit formal approving reviews. A repository owner must grant at least Write to an intended independent reviewer; do not grant Admin merely to enable reviews.
- PR #14 contains `docs/REPOSITORY-ADMIN-SETUP.md` with the exact proposed main ruleset and required checks. This document does not apply settings; an owner must configure and verify them in GitHub Settings.

Do not tag or publish a release candidate until independent reviews, required checks, branch protection, merged implementation scope, and the target version are confirmed.

## 6. Contributor handoff protocol

Before pausing, post on the relevant issue or PR:

- **Status:** exploring / in progress / blocked / ready for review / paused
- **Last completed:** exact commit, file, test, or decision
- **Next smallest step:** one actionable task
- **Branch / PR:** link
- **Blockers:** evidence and required action
- **Risks / touched files:** possible conflicts
- **Resume instructions:** exact command or location

Any authorized contributor can resume from the public checkpoint without access to another agent's private conversation. Never force-push or discard another contributor's work without explicit coordination.

## 7. Immediate sequence

1. Repository owner grants Write (or Maintain, if justified) to at least one independent reviewer account and confirms reviewer identity.
2. Repository owner activates the `main-release-protection` ruleset from `docs/REPOSITORY-ADMIN-SETUP.md`: require one independent approval, dismiss stale approvals, resolve conversations, require the quality/package/CodeQL checks, block force-push and deletion, and avoid routine bypass.
3. Repository owner enables the dependency graph, Dependabot alerts/security updates, secret scanning, and push protection where available; verify the dependency review check passes.\n4. Independent reviewers review PRs #9, #13, #14, #15, and #16; address findings and rerun checks after changes.
5. Merge the reviewed PRs in a deliberate order, resolving conflicts and rerunning checks against the resulting main commit.
6. Confirm the next candidate version; update package metadata and release notes together. The existing `0.1.0` package version and `v0.1.0-alpha` tag are historical and must not be silently overwritten.
7. Create a new version tag only from the exact verified main commit; confirm the tag-triggered workflow publishes the GitHub prerelease with wheel, sdist, and `SHA256SUMS`.
8. Verify published checksums and installation; record tag, commit, workflow, artifact names, and release URL.
9. Continue the durable broker and governed-storage slices only after their interfaces and security boundaries are independently reviewed.

## 8. Healthy handoff definition

A new authorized agent can identify the goal, read the architecture and current checkpoint, recover the allowed task context, reproduce the tests, inspect the exact branch/commit, and continue without needing a private prior session. Progress is measured by verified, attributable, resumable work—not by account or agent count.
