# Repository Administration — Main Branch Lock

**Status:** required owner configuration; this document does not change GitHub settings.

The GitHub connection used for project edits can create branches, commits, pull requests, and inspect checks, but it cannot administer repository rulesets or collaborator permissions. A repository owner must apply the following settings in GitHub.

## 1. Protect `main`

Open **Settings → Rules → Rulesets → New branch ruleset**.

- Name: `main-release-protection`
- Enforcement: `Active`
- Target branch: `main`
- Require a pull request before merging.
- Require at least **1 approving review** from someone other than the PR author.
- Dismiss stale approvals when new commits are pushed.
- Require conversation resolution before merging.
- Require status checks to pass before merging.
- Block force pushes.
- Block branch deletion.
- Do not allow bypass for routine contributors. If an administrator emergency bypass is retained, require a documented reason and follow-up review.

Add these required checks after the workflows are present on the default branch:

| Workflow / job | Why it is required |
|---|---|
| `Quality and package / quality` | Ruff lint/format, Bandit, pip-audit, unit tests, demo smoke test |
| `Quality and package / package` | source/wheel build, isolated install smoke test, checksummed artifacts |
| `Analyze Python` | CodeQL security-extended analysis |

GitHub may show check names only after each workflow has reported at least once on the default branch. Select the exact names displayed in the ruleset UI.

## 2. Reviewer permissions

A formal approving review requires repository write access. Current observed permissions for `HuffmanMainNode` and `Ryzean84` are **read**.

If either account is an intended maintainer/reviewer, open **Settings → Collaborators and teams** and grant the minimum required permission:

- `Write` is sufficient to submit reviews and contribute through branches/PRs.
- `Maintain` is appropriate for delegated repository maintenance.
- `Admin` should be reserved for accounts that must change repository settings, access, rulesets, or security configuration.

Do not grant Admin solely to enable PR review. Keep at least one independent reviewer who is not the PR author.

## 3. Release controls

- Keep release publication restricted to versioned release-candidate tags matching `v*-rc.*`.
- Create tags only from the exact verified `main` commit.
- Confirm the release workflow passed and the GitHub prerelease contains the wheel, source archive, and `SHA256SUMS`.
- Verify checksums after download.
- Keep production credentials and signing keys out of source, issue comments, workflow logs, and build artifacts.

## 4. Completion evidence

After applying settings, record in the shared checkpoint:

- ruleset name and target branch;
- required check names;
- approval count and conversation-resolution setting;
- reviewer accounts and permission levels;
- date applied and owner confirmation.

A ruleset is not considered active merely because this document exists. Verify the ruleset in GitHub Settings and test it with a non-admin PR before claiming `main` is protected.
