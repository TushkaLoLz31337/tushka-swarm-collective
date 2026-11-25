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


## 3. Security and dependency controls

Open **Settings → Security and analysis** and verify the following for this public repository:

- Enable the dependency graph.
- Enable Dependabot alerts and security updates.
- Confirm secret scanning is active and alerts are visible to maintainers.
- Enable repository push protection where the repository's available plan/settings permit it; user-level push protection is not a substitute for checking repository-level alert configuration.
- Keep CodeQL code scanning enabled and review alerts rather than treating a green workflow as proof that no vulnerabilities exist.
- Enable private vulnerability reporting so researchers can report findings without publishing exploit details.
- Review GitHub Actions permissions and restrict third-party actions to trusted publishers; pin actions to full commit SHAs as a follow-up hardening task.

The CI workflow now includes a Dependency Review check for pull requests and Dependabot configuration for weekly pip and GitHub Actions updates. These checks do not replace the repository's security settings or a human review of dependency changes.

GitHub documents that dependency graph, Dependabot alerts, secret scanning, push protection, and code scanning are important controls for public repositories; feature availability and defaults vary by control. See [GitHub security settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-security-and-analysis-settings-for-your-repository) and [GitHub security features](https://docs.github.com/en/code-security/getting-started/github-security-features).

## 4. Release controls

- Keep release publication restricted to versioned release-candidate tags matching `v*-rc.*`.
- Create tags only from the exact verified `main` commit.
- Confirm the release workflow passed and the GitHub prerelease contains the wheel, source archive, and `SHA256SUMS`.
- Verify checksums after download.
- Keep production credentials and signing keys out of source, issue comments, workflow logs, and build artifacts.

## 5. Completion evidence

After applying settings, record in the shared checkpoint:

- ruleset name and target branch;
- required check names, including `Dependency review`;
- approval count and conversation-resolution setting;
- reviewer accounts and permission levels;
- date applied and owner confirmation;\n- dependency graph, Dependabot alerts/security updates, secret scanning, push protection, and private vulnerability reporting status.

A ruleset is not considered active merely because this document exists. Verify the ruleset in GitHub Settings and test it with a non-admin PR before claiming `main` is protected.
