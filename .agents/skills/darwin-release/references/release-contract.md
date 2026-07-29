# DARWIN Source-Release Contract

## Contents

1. Release invariants
2. Read-only planning evidence
3. Decision-complete plan
4. Approved implementation
5. Release gates and factualization
6. Pull request, CI, and merge
7. Tag and publication
8. Preservation and cleanup
9. Date-boundary rules
10. Failure policy

## 1. Release Invariants

Preserve these defaults unless the user explicitly approves a different
release contract:

- simulator-local, deterministic, symbolic, and source-only behavior;
- no package-index publication;
- no uploaded GitHub release assets;
- Python 3.11 through 3.14 CI;
- a separate Python 3.11 wheel build/install smoke job;
- exact CLI output `darwin-sim <version>`;
- globally contiguous three-digit scenario numbering;
- exact generated-versus-checked-in `docs/SCENARIO_INDEX.md`;
- `_DRAFT` release-note filenames retained permanently for link compatibility;
- actual America/Los_Angeles date and final pytest count recorded only after
  the first complete passing release gates;
- no modification of released tags, releases, commits, or historical notes;
- no force-push, history rewrite, tag movement, or unsafe branch deletion;
- unrelated user changes preserved; and
- no feature-scope expansion during release hardening.

Treat wheels as validation artifacts only. Building a wheel does not authorize
uploading or publishing it.

## 2. Read-Only Planning Evidence

Do not fetch during planning. Use read-only commands and GitHub API/CLI calls:

```text
git status
git log
git show
git branch
git tag
git ls-remote
gh repo view
gh pr list
gh release list
gh release view
gh run list
gh api
```

Verify rather than assume:

- current branch and clean worktree;
- local `main`, existing `origin/main`, and live GitHub `main`;
- latest version, release, annotated tag object, and peeled commit;
- all local and remote branches;
- all historical tags and GitHub release IDs;
- open pull requests;
- release assets;
- package-index status;
- latest completed release gates and CI matrix; and
- existing roadmap or deferred scope.

Inspect at minimum:

- implementation and public models/helpers/registries;
- runner, scenario DSL, assertions, snapshots, serialization, and CLI;
- focused, regression, scenario, smoke, and release-readiness tests;
- README, changelog, roadmap, specifications, release notes, and checklist;
- `docs/SCENARIO_INDEX.md` and its generator;
- `.github/workflows/ci.yml`; and
- explicit exclusions and non-goals.

## 3. Decision-Complete Plan

When no explicit scope exists, recommend two or three bounded,
repository-grounded options. Compare:

- compatibility with current public contracts;
- implementation and serialization risk;
- scenario/test/doc impact;
- interaction with deferred non-goals; and
- release-readiness risk.

Identify a preferred option and obtain approval.

The plan must state:

- summary and release theme;
- exact public contracts and compatibility requirements;
- models, helpers, registries, DSL, snapshots, serialization, and CLI affected;
- unit, regression, scenario, documentation, and release testing;
- the next contiguous scenario numbers;
- documentation and generated-index changes;
- version and CI changes;
- explicit exclusions;
- release and cleanup sequence;
- risks and assumptions; and
- every decision requiring approval.

## 4. Approved Implementation

After approval:

1. Require a clean worktree. Stop rather than overwrite unrelated changes.
2. Run `git fetch --prune origin`.
3. Fast-forward local `main` with `git merge --ff-only origin/main`.
4. Require local `main`, `origin/main`, and `git ls-remote` live `main` to
   match.
5. Record baseline inventories before any release mutation.
6. Create `codex/v<major>.<minor>-release` from exact `main` for a normal
   `<major>.<minor>.0` release; include the patch component when needed to
   avoid ambiguity. Use another branch name only when the user approves it.
7. Implement only the approved feature and compatibility slice.
8. Add scenarios beginning at the next global number with no gaps.
9. Update all current scenario-ceiling expectations while preserving
   historical scenario-specific behavior.
10. Generate the scenario index only from:

```text
python -m darwin.cli.main scenario-index
```

Never hand-edit generated scenario rows. Preserve both the exact Python
string-equality test and CI file comparison.

Update:

- package and `darwin.__version__`;
- exact source and wheel CLI expectations;
- README and changelog;
- roadmap and specification;
- release notes and checklist;
- scenario DSL and index;
- release-readiness tests; and
- CI version assertions.

Before factualization, use explicit pending-validation language. Do not predict
the date or test count.

Create the preparation commit with the user-approved subject, normally:

```text
Prepare DARWIN v<version> release
```

## 5. Release Gates and Factualization

Run:

```text
python -m ruff check .
python -m pytest
python scripts/run_all_scenarios.py
python -m darwin.cli.main scenario-index
python -m darwin.cli.main --version
python -m build --wheel
```

Also:

- compare generated scenario-index output exactly with
  `docs/SCENARIO_INDEX.md`;
- install the exact versioned wheel in an isolated environment;
- run the installed-wheel CLI from outside the repository; and
- require exact output `darwin-sim <version>`.

After every gate first passes as one complete set:

1. take the pytest total from that passing suite;
2. read the current America/Los_Angeles date;
3. insert both facts consistently in release-facing docs and assertions;
4. do not add or remove tests during factualization;
5. rerun every gate; and
6. repeat factualization if the count is not self-consistent.

Create the factualization commit with the user-approved subject, normally:

```text
Finalize DARWIN v<version> release date
```

## 6. Pull Request, CI, and Merge

Push the release branch without force. Open a ready-for-review PR titled:

```text
Release DARWIN v<version>
```

The PR body must record:

- approved scope and compatibility effects;
- exact local validation and final pytest count;
- scenario range and exact-index result;
- source and installed-wheel CLI output;
- Python CI and separate wheel-smoke expectations; and
- source-only, no-assets, no-package publication.

Wait for every push and PR job. Require Python 3.11 through 3.14 and wheel
smoke to pass on the exact final head SHA.

Before merge, recheck the America/Los_Angeles date. If it changed, update the
open PR and rerun gates/CI.

Use a merge commit with:

```text
subject: Release v<version>
body: Merge the validated v<version> source-release snapshot.
```

After merge:

1. fetch/prune and fast-forward local `main`;
2. require local, tracking, and live GitHub `main` to equal the merge SHA;
3. verify the merge subject, body, and two parents;
4. rerun every release gate on that exact commit;
5. require a clean worktree; and
6. wait for every exact-SHA main job.

## 7. Tag and Publication

Recheck the America/Los_Angeles date before tagging. If it changed after merge
but before tagging, use a bounded date-correction branch and PR, rerun all
gates/CI, and tag the corrected merge commit.

Require the version tag to be absent locally and remotely. Create:

```text
git tag -a v<version> <exact-main-sha> -m "DARWIN v<version>"
```

Push only `refs/tags/v<version>`. Verify:

- the remote tag object;
- the peeled target equals exact merged `main`; and
- every tag-triggered CI job passes.

Immediately before publication, recheck the date. If it changed after the tag
was pushed, fail closed and request user authority. Never move or delete the
released tag.

Publish the latest GitHub release:

- title `DARWIN v<version>`;
- existing annotated tag;
- body from checked-in final `_DRAFT` notes;
- no package publication; and
- no uploaded assets.

Verify through the public API:

- title, tag, body equality, draft/prerelease/latest status;
- empty assets;
- annotated tag object and peeled target;
- local/tracking/live `main`;
- source and installed-wheel CLI versions;
- package-index non-publication by this workflow; and
- clean worktree.

## 8. Preservation and Cleanup

Compare the final state against the pre-release inventories:

- every historical tag object and peeled target is unchanged;
- every historical GitHub release ID is unchanged;
- all historical releases remain present;
- the new tag and release increase totals by exactly one; and
- no unexpected assets or branches exist.

Before branch deletion, record the release-branch tip and require:

```text
git merge-base --is-ancestor <release-branch> main
git rev-list --count main..<release-branch>
```

The unique count must be zero locally and remotely. Do not require symmetric
zero because the merge commit exists only on `main`.

While on `main`:

1. delete locally with `git branch -d`;
2. delete remotely only after the audit;
3. fetch/prune tracking refs; and
4. confirm only local `main`, only live remote `main`, no open PRs, preserved
   tags/releases, synchronized main, and a clean worktree.

## 9. Date-Boundary Rules

- Before merge: update the open PR and revalidate.
- After merge but before tag: use a correction PR and revalidate.
- After tag push: stop and request authority; do not move/delete the tag.
- Before release publication: always perform an immediate date check.

Never predict or pre-fill a future release date.

## 10. Failure Policy

Do not bypass or weaken:

- authentication and authorization;
- branch protection;
- required CI;
- exact-index comparison;
- wheel isolation;
- historical preservation;
- safe ancestry checks; or
- approval boundaries.

Do not broaden the feature to solve release-gate failures. Fix only the
approved scope, compatibility regressions, tests, docs, versions, or CI
contract. Report external blockers precisely and leave released history
untouched.
