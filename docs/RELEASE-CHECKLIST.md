# Release Candidate Checklist

This checklist is a hard gate for every release candidate. A tag must point to the exact main commit whose checks passed.

## Before tagging

- [ ] Confirm the target version and release channel; match pyproject.toml, release notes, and tag. For a PEP 440 candidate such as `0.2.0rc1`, use the matching tag `v0.2.0-rc.1`.
- [ ] Review and merge all intended PRs; no unreviewed or conflicted work is included.
- [ ] Ensure main is protected with required independent review and required CI/security checks, including dependency review.
- [ ] Run Ruff lint and format checks.
- [ ] Run the complete unit and demo test suite.
- [ ] Run Bandit and CodeQL security analysis.
- [ ] Confirm GitHub secret scanning is active and review open alerts.
- [ ] Confirm dependency review passes and Dependabot alerts are triaged.
- [ ] Run pip-audit against pinned CI and test dependencies.
- [ ] Build both source distribution and wheel.
- [ ] Install the wheel in an isolated target and run the demo.
- [ ] Generate SHA-256 checksums and preserve the build artifact.
- [ ] Review README, roadmap, checkpoint, release notes, license, and known limitations.
- [ ] Confirm no secrets, private data, or unreviewed third-party code are included.
- [ ] Confirm the use-case and compliance register accurately describes what is enabled and what remains prohibited/deferred.

## Tag and publish

- [ ] Create the tag from the verified main commit only. The release workflow independently verifies that the tagged commit equals the exact current `main` commit and that the tag matches the package version.
- [ ] Confirm the tag-triggered workflow passes all required jobs.
- [ ] Confirm the GitHub prerelease contains the wheel, source archive, and SHA256SUMS.
- [ ] Verify downloaded checksums against the published assets.
- [ ] Record tag, commit SHA, workflow run, artifact names, and release URL in the shared checkpoint.

## After publication

- [ ] Test installation from the published wheel and source archive.
- [ ] Confirm the release page accurately labels experimental features and limitations.
- [ ] Announce the release with links to source, artifacts, checksums, and contribution instructions.

A green test run is not a production security audit, legal opinion, or compliance certification. Release status must not overstate implementation maturity.
