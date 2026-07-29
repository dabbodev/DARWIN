---
name: darwin-release
description: Plan and deliver a complete DARWIN source release from read-only scope discovery through implementation, validation, pull request, CI, merge, annotated tag, GitHub release, preservation audit, and safe release-branch cleanup. Use only when explicitly invoked for a DARWIN version release, release plan, release preparation, publication, or post-release audit; never invoke implicitly.
---

# DARWIN Release

Run DARWIN's approval-gated source-release workflow without skipping the
publication or cleanup phases. Treat live repository and GitHub evidence as
authoritative.

## Required Reference

Read `references/release-contract.md` completely before inspecting or changing
release state. Follow its exact gates, sequencing, and stop conditions.

## Inputs

Resolve these from the user's request and current repository evidence:

- target version or semver decision;
- approved feature theme and exclusions;
- current released version, scenario ceiling, tags, releases, and main SHA;
- release-specific compatibility requirements; and
- any explicit exceptions to the standard source-only contract.

Do not infer permission to publish packages, upload assets, rewrite history,
move tags, force-push, or broaden feature scope.

## Phase 1: Read-Only Planning

Begin every new release task with a read-only planning phase, even when the
user asks for the next release generally. If the current thread already
contains a decision-complete plan and explicit approval, verify that evidence
and continue to Phase 2 without repeating the plan. In a new thread, do not
accept an unverified claim that an unseen plan was approved.

1. Require a clean understanding of the checkout and inspect local state.
2. Verify live GitHub state with read-only commands. Do not fetch yet.
3. Inspect the current implementation, tests, scenarios, scenario DSL/index,
   CI, roadmap, specifications, changelog, release notes, checklist, and
   explicitly deferred non-goals.
4. If no release scope is explicit, recommend two or three repository-grounded
   options with compatibility and implementation risks.
5. Produce a decision-complete plan covering contracts, affected surfaces,
   tests, scenarios, documentation, CI, release procedure, exclusions, risks,
   assumptions, and decisions.
6. Stop and obtain explicit user approval for the release direction and
   mutation phase.

Do not edit files, fetch refs, create branches, commit, push, open or merge a
pull request, tag, publish, or delete anything during this phase.

## Phase 2: Approved Delivery

Enter this phase only after the user explicitly approves the plan.

1. Revalidate the worktree. Preserve unrelated changes and stop if they
   overlap or make the release unsafe.
2. Fetch/prune safely, fast-forward `main` only, and require local, tracking,
   and live GitHub `main` to agree.
3. Snapshot branch, tag object/peeled target, release ID/assets, open-PR,
   package-index, and relevant CI inventories.
4. Create the release branch from exact `main`.
5. Implement only the approved scope, compatibility protections, tests,
   contiguous scenarios, docs, versions, and CI expectations.
6. Commit the preparation snapshot before recording a test count or date.
7. Run every release gate. Fix failures without broadening scope.
8. Record the actual pytest count and America/Los_Angeles date only after the
   first complete passing gate set. Rerun all gates and commit factualization.
9. Push without force, open a ready PR, document validation and publication
   limits, wait for push and PR CI, then merge with the approved merge-commit
   subject and body.
10. Fast-forward local `main`, revalidate the exact merged SHA locally, and
    wait for exact-SHA main CI.
11. Recheck the release date, create and push only the annotated version tag,
    verify its peeled target, and wait for tag CI.
12. Recheck the date immediately before publication, then publish the latest
    GitHub source release from checked-in notes with no package or assets.
13. Verify public release state and all historical preservation invariants.
14. Prove the release branch is fully merged with zero unique commits, delete
    it safely locally and remotely, prune, and perform the final audit.

Do not stop after implementation, local tests, PR creation, merge, or tagging
while an approved and safe next step remains.

## Stop Conditions

Fail closed and request user action or authority when:

- unrelated work cannot be preserved safely;
- GitHub authentication or required permissions are unavailable;
- branch protection or CI prevents the approved sequence;
- local, tracking, and live refs disagree unexpectedly;
- a historical tag, release ID, or released commit would change;
- publication would cross the recorded date after the immutable tag exists;
- a package, asset, history rewrite, force-push, unsafe deletion, or scope
  expansion would be required; or
- the approved release contract cannot be verified.

## Completion Report

Report the release URL, PR, merge SHA, annotated tag object and peeled target,
release ID, actual date/test/scenario counts, all local and GitHub validation,
publication limits, preservation totals, branch cleanup, remaining warnings,
and final clean/synchronized state. Clearly distinguish completed facts from
anything not performed.
