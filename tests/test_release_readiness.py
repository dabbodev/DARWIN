import re
import tomllib
from pathlib import Path

import darwin

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V1_3_PLANNING_DOCS = [
    PROJECT_ROOT / "docs" / "V1_3_ROADMAP.md",
    PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_3_DRAFT.md",
    PROJECT_ROOT / "docs" / "STREAM_OFFER_LIFECYCLE_HISTORY_v1_3.md",
    PROJECT_ROOT / "docs" / "STREAM_OFFER_LIFECYCLE_PLANNING_v1_3.md",
]
V1_4_RELEASE_PREP_DOCS = [
    PROJECT_ROOT / "docs" / "V1_4_ROADMAP.md",
    PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_4_DRAFT.md",
    PROJECT_ROOT / "docs" / "STREAM_OFFER_LIFECYCLE_EXPLANATIONS_v1_4.md",
    PROJECT_ROOT / "docs" / "STREAM_OFFER_LIFECYCLE_AUDIT_SUMMARIES_v1_4.md",
    PROJECT_ROOT / "docs" / "STREAM_OFFER_LIFECYCLE_EXPLANATION_HISTORY_v1_4.md",
]
V1_5_RELEASE_CANDIDATE_DOCS = [
    PROJECT_ROOT / "docs" / "V1_5_ROADMAP.md",
    PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_5_DRAFT.md",
    PROJECT_ROOT / "docs" / "STREAM_OFFER_LIFECYCLE_EXPLANATION_RETENTION_v1_5.md",
    PROJECT_ROOT / "docs" / "STREAM_OFFER_LIFECYCLE_EXPLANATION_PRUNING_v1_5.md",
]
V1_6_RELEASE_CANDIDATE_DOCS = [
    PROJECT_ROOT / "docs" / "V1_6_ROADMAP.md",
    PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_6_DRAFT.md",
    PROJECT_ROOT / "docs" / "RETAINED_AUDIT_COMPACTION_POLICY_v1_6.md",
    PROJECT_ROOT / "docs" / "RETAINED_AUDIT_REPLAY_SUMMARIES_v1_6.md",
    PROJECT_ROOT / "docs" / "RETAINED_AUDIT_COMPACTION_APPLY_v1_6.md",
]
V1_7_RELEASE_SNAPSHOT_DOCS = [
    PROJECT_ROOT / "docs" / "V1_7_ROADMAP.md",
    PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_7_DRAFT.md",
    PROJECT_ROOT / "docs" / "RETAINED_AUDIT_POLL_ADMISSION_v1_7.md",
]
V1_8_RELEASE_SNAPSHOT_DOCS = [
    PROJECT_ROOT / "docs" / "V1_8_ROADMAP.md",
    PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_8_DRAFT.md",
    PROJECT_ROOT / "docs" / "RETAINED_AUDIT_ENCRYPTED_DELIVERY_v1_8.md",
]
V1_9_RELEASE_SNAPSHOT_DOCS = [
    PROJECT_ROOT / "docs" / "V1_9_ROADMAP.md",
    PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_9_DRAFT.md",
    PROJECT_ROOT / "docs" / "RETAINED_AUDIT_ENCRYPTION_POLICY_v1_9.md",
]
V1_3_RELEASE_CANDIDATE_CAVEATS = [
    "simulator-local",
    "symbolic",
    "real networking",
    "sockets",
    "DNS lookup",
    "external services",
    "real cryptography",
    "production E2EE",
    "production anonymity",
    "production privacy",
    "production firewall",
    "production DDoS",
    "automatic cleanup workers",
    "retry loops",
    "durable queues",
    "live timers",
    "TrafficHub routing changes",
    "delivery behavior changes",
    "compact snapshot changes",
    "canonical identity rewrites",
]
V1_4_RELEASE_CANDIDATE_CAVEATS = [
    "simulator-local",
    "symbolic",
    "real networking",
    "sockets",
    "DNS lookup",
    "external services",
    "real cryptography",
    "production E2EE",
    "production anonymity",
    "production privacy",
    "production firewall",
    "production DDoS",
    "automatic cleanup workers",
    "retry loops",
    "durable queues",
    "live timers",
    "live polling",
    "lifecycle mutation behavior",
    "TrafficHub routing changes",
    "delivery behavior changes",
    "compact snapshot changes",
    "canonical identity rewrites",
]
V1_5_RELEASE_CANDIDATE_CAVEATS = [
    "simulator-local",
    "symbolic",
    "real networking",
    "sockets",
    "DNS lookup",
    "external services",
    "real cryptography",
    "production E2EE",
    "production anonymity",
    "production privacy",
    "production firewall",
    "production DDoS",
    "automatic cleanup workers",
    "retry loops",
    "durable queues",
    "live timers",
    "live clocks",
    "live polling",
    "retention/pruning behavior beyond explicit simulator helpers",
    "TrafficHub routing changes",
    "delivery behavior changes",
    "compact snapshot changes",
    "canonical identity rewrites",
]
V1_6_RELEASE_CANDIDATE_CAVEATS = [
    "simulator-local",
    "symbolic",
    "real networking",
    "sockets",
    "DNS lookup",
    "external services",
    "real cryptography",
    "production E2EE",
    "production anonymity",
    "production privacy",
    "production firewall",
    "production DDoS",
    "compliance",
    "data-retention guarantees",
    "automatic cleanup workers",
    "retry loops",
    "durable queues",
    "live timers",
    "live clocks",
    "live polling",
    "compaction behavior beyond explicit simulator helpers",
    "TrafficHub routing changes",
    "delivery behavior changes",
    "compact snapshot changes",
    "canonical identity rewrites",
]
V1_7_RELEASE_SNAPSHOT_CAVEATS = [
    "simulator-local",
    "symbolic",
    "real networking",
    "sockets",
    "HTTP/WebSocket",
    "DNS lookup",
    "external services",
    "real cryptography",
    "production E2EE",
    "automatic cleanup",
    "retry loops",
    "durable queues",
    "live timers",
    "live clocks",
    "live polling",
    "delivery enforcement",
    "TrafficHub routing changes",
    "compact snapshot changes",
    "canonical identity rewrites",
    "compliance",
    "data-retention guarantees",
]
V1_8_RELEASE_SNAPSHOT_CAVEATS = [
    "simulator-local",
    "symbolic",
    "real networking",
    "DNS",
    "external services",
    "real cryptography",
    "production E2EE",
    "automatic cleanup",
    "retries",
    "durable queues",
    "live timers",
    "delivery enforcement",
    "TrafficHub routing changes",
    "compact snapshot changes",
    "canonical identity rewrites",
    "compliance",
    "data-retention guarantees",
]
V1_9_RELEASE_SNAPSHOT_CAVEATS = [
    "simulator-local",
    "deterministic",
    "source-only",
    "real networking",
    "DNS",
    "external services",
    "real cryptography",
    "production E2EE",
    "automatic cleanup",
    "workers",
    "retries",
    "durable queues",
    "live timers",
    "live clocks",
    "live polling",
    "delivery enforcement",
    "TrafficHub routing changes",
    "compact snapshot changes",
    "canonical identity rewrites",
    "compliance",
    "data-retention guarantees",
]


def _repo_relative_backtick_paths(text: str) -> set[str]:
    paths = set()
    for match in re.findall(r"`([^`]+)`", text):
        candidate = match.strip()
        if candidate.startswith(("docs/", "scenarios/", ".github/")):
            paths.add(candidate)
    return paths


def test_documentation_links_exist():
    checked_docs = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "docs" / "DEMO_GUIDE_v0_1.md",
        PROJECT_ROOT / "docs" / "DEVELOPMENT.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_1.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_2.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_3.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_4.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_5.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_6_DRAFT.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_7_DRAFT.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_8_DRAFT.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_9_DRAFT.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_0_DRAFT.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_1_DRAFT.md",
        PROJECT_ROOT / "docs" / "V1_2_ROADMAP.md",
        PROJECT_ROOT / "docs" / "STREAM_OFFERS_v1_2.md",
        PROJECT_ROOT / "docs" / "RENDEZVOUS_OFFER_QUEUES_v1_2.md",
        PROJECT_ROOT / "docs" / "PRIVATE_POLLING_DESCENT_v1_2.md",
        PROJECT_ROOT / "docs" / "LANE_ADMISSION_POLICY_v1_2.md",
        PROJECT_ROOT / "docs" / "STREAM_OFFER_AUDIT_HISTORY_v1_2.md",
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_2_DRAFT.md",
        *V1_3_PLANNING_DOCS,
        *V1_4_RELEASE_PREP_DOCS,
        *V1_5_RELEASE_CANDIDATE_DOCS,
        *V1_6_RELEASE_CANDIDATE_DOCS,
        *V1_7_RELEASE_SNAPSHOT_DOCS,
        *V1_8_RELEASE_SNAPSHOT_DOCS,
        *V1_9_RELEASE_SNAPSHOT_DOCS,
    ]

    referenced_paths = {
        "docs/ARCHITECTURE_v0_1.md",
        "docs/V0_2_ROADMAP.md",
        "docs/RELEASE_NOTES_v0_1.md",
    }
    for doc_path in checked_docs:
        referenced_paths.update(
            _repo_relative_backtick_paths(doc_path.read_text(encoding="utf-8"))
        )

    missing = sorted(
        path for path in referenced_paths if not (PROJECT_ROOT / path).exists()
    )
    assert missing == []


def test_version_consistency():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = pyproject["project"]["version"]
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release_notes = (PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_1.md").read_text(
        encoding="utf-8"
    )
    current_release_notes = (
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_9_DRAFT.md"
    ).read_text(encoding="utf-8")

    assert darwin.__version__ == project_version
    assert f"[{project_version}]" in changelog or f"## v{project_version}" in changelog
    assert f"v{project_version}" in current_release_notes
    assert "darwin-sim 1.9.0" in current_release_notes
    assert "Scenarios `076` through `078`" in current_release_notes
    assert "real networking" in current_release_notes
    assert "TrafficHub routing changes" in current_release_notes
    assert "v0.1.0" in release_notes


def test_v1_3_docs_are_release_status_ready():
    release_notes = (PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_3_DRAFT.md").read_text(
        encoding="utf-8"
    )
    roadmap = (PROJECT_ROOT / "docs" / "V1_3_ROADMAP.md").read_text(
        encoding="utf-8"
    )
    combined_docs = "\n".join(path.read_text(encoding="utf-8") for path in V1_3_PLANNING_DOCS)

    assert "released on `main` as `darwin-sim 1.3.0`" in release_notes
    assert "Sprints 1 through 6" in release_notes
    assert "darwin-sim 1.3.0" in release_notes
    assert "Scenarios `058` through `060`" in release_notes
    assert "from `001` through `060`" in release_notes
    assert "https://github.com/dabbodev/DARWIN/releases/tag/v1.3.0" in release_notes
    assert "No package publication was performed" in release_notes
    assert "no release assets were uploaded" in release_notes
    assert "python -m pytest` with 808 tests" in release_notes
    assert "Sprint 6: Release-Candidate Hardening" in roadmap

    for caveat in V1_3_RELEASE_CANDIDATE_CAVEATS:
        assert caveat in combined_docs


def test_v1_4_docs_are_release_status_ready():
    release_notes = (PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_4_DRAFT.md").read_text(
        encoding="utf-8"
    )
    roadmap = (PROJECT_ROOT / "docs" / "V1_4_ROADMAP.md").read_text(
        encoding="utf-8"
    )
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (PROJECT_ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    combined_docs = "\n".join(
        path.read_text(encoding="utf-8") for path in V1_4_RELEASE_PREP_DOCS
    )

    assert "released on `main` as `darwin-sim 1.4.0`" in release_notes
    assert "https://github.com/dabbodev/DARWIN/releases/tag/v1.4.0" in release_notes
    assert "No package publication was performed" in release_notes
    assert "no release assets were uploaded" in release_notes
    assert "Sprint 1 through Sprint 6" in release_notes
    assert "Scenarios `061` through `063`" in release_notes
    assert "checked-in scenarios through `063`" in release_notes
    assert (
        "v1.4 release prep set the package and CLI version to `darwin-sim 1.4.0`"
        in release_notes
    )
    assert "The final v1.4.0 validation passed" in release_notes
    assert "python -m pytest` with 836 tests" in release_notes
    assert "DARWIN v1.4 is released on `main` as `darwin-sim 1.4.0`" in roadmap
    assert "Sprint 6: Release-Candidate Hardening" in roadmap
    assert "scenarios `061` through" in readme
    assert "through `063`" in readme
    assert "v1.4.0 is released on `main` as `darwin-sim 1.4.0`" in checklist

    for caveat in V1_4_RELEASE_CANDIDATE_CAVEATS:
        assert caveat in combined_docs


def test_v1_5_docs_are_release_status_ready():
    release_notes = (PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_5_DRAFT.md").read_text(
        encoding="utf-8"
    )
    roadmap = (PROJECT_ROOT / "docs" / "V1_5_ROADMAP.md").read_text(
        encoding="utf-8"
    )
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (PROJECT_ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    combined_docs = "\n".join(
        path.read_text(encoding="utf-8") for path in V1_5_RELEASE_CANDIDATE_DOCS
    )
    combined_docs_normalized = re.sub(r"\s+", " ", combined_docs)

    assert "released on `main` as `darwin-sim 1.5.0`" in release_notes
    assert "https://github.com/dabbodev/DARWIN/releases/tag/v1.5.0" in release_notes
    assert "No package publication was performed" in combined_docs_normalized
    assert "no release assets were uploaded" in combined_docs_normalized
    assert "Sprint 1 through Sprint 6" in release_notes
    assert "Scenarios `064` through `066`" in release_notes
    assert "from `001` through `066`" in release_notes
    assert "Release-candidate hardening" in release_notes
    assert "darwin-sim 1.5.0" in release_notes
    assert "Release readiness has not started" not in release_notes
    assert "Sprint 6: Release-Candidate Hardening and Documentation Audit" in roadmap
    assert "release-candidate hardening and documentation audit only" in roadmap
    assert "Release prep set the package and CLI version to `darwin-sim 1.5.0`" in roadmap
    assert "released on `main` as `darwin-sim 1.5.0`" in roadmap
    assert "docs/STREAM_OFFER_LIFECYCLE_EXPLANATION_PRUNING_v1_5.md" in readme
    assert "v1.5 release-candidate hardening" in checklist
    assert "v1.5.0 is released on `main` as `darwin-sim 1.5.0`" in checklist

    for caveat in V1_5_RELEASE_CANDIDATE_CAVEATS:
        assert caveat in combined_docs_normalized


def test_v1_6_docs_are_release_status_ready():
    release_notes = (PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_6_DRAFT.md").read_text(
        encoding="utf-8"
    )
    roadmap = (PROJECT_ROOT / "docs" / "V1_6_ROADMAP.md").read_text(
        encoding="utf-8"
    )
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (PROJECT_ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    combined_docs = "\n".join(
        path.read_text(encoding="utf-8") for path in V1_6_RELEASE_CANDIDATE_DOCS
    )
    combined_docs_normalized = re.sub(r"\s+", " ", combined_docs)

    assert "released on `main` as `darwin-sim 1.6.0`" in release_notes
    assert "https://github.com/dabbodev/DARWIN/releases/tag/v1.6.0" in release_notes
    assert "No package publication was performed" in combined_docs_normalized
    assert "no release assets were uploaded" in combined_docs_normalized
    assert "Sprint 1 through Sprint 6" in release_notes
    assert "Sprint 6: Release-Candidate Hardening and Documentation Audit" in release_notes
    assert "Sprint 6: Release-Candidate Hardening and Documentation Audit" in roadmap
    assert "release-candidate hardening and documentation audit only" in roadmap
    assert "darwin-sim 1.6.0" in combined_docs_normalized
    assert "from `001` through `069`" in release_notes
    assert "docs/RETAINED_AUDIT_COMPACTION_APPLY_v1_6.md" in readme
    assert "Release prep set the package and CLI version to `darwin-sim 1.6.0`" in roadmap
    assert "released on `main` as `darwin-sim 1.6.0`" in roadmap
    assert "v1.6 release-candidate hardening and documentation audit" in checklist
    assert "from `001` through `069`" in checklist
    assert "v1.6.0 is released on `main` as `darwin-sim 1.6.0`" in checklist

    for caveat in V1_6_RELEASE_CANDIDATE_CAVEATS:
        assert caveat in combined_docs_normalized


def test_v1_7_docs_describe_the_source_release_snapshot():
    release_notes = (
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_7_DRAFT.md"
    ).read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs" / "V1_7_ROADMAP.md").read_text(
        encoding="utf-8"
    )
    specification = (
        PROJECT_ROOT / "docs" / "RETAINED_AUDIT_POLL_ADMISSION_v1_7.md"
    ).read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (PROJECT_ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    combined_docs = "\n".join(
        path.read_text(encoding="utf-8") for path in V1_7_RELEASE_SNAPSHOT_DOCS
    )
    combined_docs_normalized = re.sub(r"\s+", " ", combined_docs)

    assert "v1.7.0 source-release snapshot" in release_notes
    assert "darwin-sim 1.7.0" in combined_docs_normalized
    assert "does not claim" in release_notes
    assert "releases/tag/v1.7.0" not in combined_docs
    assert "No package-index publication is performed" in release_notes
    assert "No release assets are uploaded" in release_notes
    assert "Scenarios `070` through `072`" in release_notes
    assert "from `001` through `072`" in release_notes
    assert "by_request_id" in specification
    assert "matched_offer_ids" in specification
    assert "mixed or unsupported decision" in specification
    assert "Python 3.11, 3.12, 3.13, and 3.14" in roadmap
    assert "docs/RETAINED_AUDIT_POLL_ADMISSION_v1_7.md" in readme
    assert "immutable v1.7.0 source snapshot" in checklist
    assert "## [1.7.0] - 2026-07-19" in changelog

    for caveat in V1_7_RELEASE_SNAPSHOT_CAVEATS:
        assert caveat in combined_docs_normalized


def test_v1_8_docs_describe_the_source_release_snapshot():
    release_notes = (
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_8_DRAFT.md"
    ).read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs" / "V1_8_ROADMAP.md").read_text(
        encoding="utf-8"
    )
    specification = (
        PROJECT_ROOT / "docs" / "RETAINED_AUDIT_ENCRYPTED_DELIVERY_v1_8.md"
    ).read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (PROJECT_ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    combined_docs = "\n".join(
        path.read_text(encoding="utf-8") for path in V1_8_RELEASE_SNAPSHOT_DOCS
    )
    combined_docs_normalized = re.sub(r"\s+", " ", combined_docs)

    assert "v1.8.0 source-release snapshot" in release_notes
    assert "darwin-sim 1.8.0" in combined_docs_normalized
    assert "does not claim" in release_notes
    assert "releases/tag/v1.8.0" not in combined_docs
    assert "No package-index publication is performed" in release_notes
    assert "No release assets are uploaded" in release_notes
    assert "Scenarios `073` through `075`" in release_notes
    assert "from `001` through `075`" in release_notes
    assert "by_message_id" in specification
    assert "by_mailbox_id" in specification
    assert 'metadata["registry_hub"]' in specification
    assert 'metadata["note"]' in specification
    assert "encrypted_delivery_history_mutated" in specification
    assert "Python 3.11 through 3.14" in roadmap
    assert "docs/RETAINED_AUDIT_ENCRYPTED_DELIVERY_v1_8.md" in readme
    assert "immutable v1.8.0 source snapshot" in checklist
    assert "## [1.8.0] - 2026-07-26" in changelog

    for caveat in V1_8_RELEASE_SNAPSHOT_CAVEATS:
        assert caveat in combined_docs_normalized


def test_v1_9_docs_describe_the_source_release_snapshot():
    release_notes = (
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v1_9_DRAFT.md"
    ).read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs" / "V1_9_ROADMAP.md").read_text(
        encoding="utf-8"
    )
    specification = (
        PROJECT_ROOT / "docs" / "RETAINED_AUDIT_ENCRYPTION_POLICY_v1_9.md"
    ).read_text(encoding="utf-8")
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (PROJECT_ROOT / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    combined_docs = "\n".join(
        path.read_text(encoding="utf-8") for path in V1_9_RELEASE_SNAPSHOT_DOCS
    )
    combined_docs_normalized = re.sub(r"\s+", " ", combined_docs)

    assert "v1.9.0 source-release snapshot" in release_notes
    assert "darwin-sim 1.9.0" in combined_docs_normalized
    assert "does not claim" in release_notes
    assert "releases/tag/v1.9.0" not in combined_docs
    assert "No package-index publication is performed" in release_notes
    assert "No release assets are uploaded" in release_notes
    assert "Release date: `2026-07-26` (America/Los_Angeles)" in release_notes
    assert "python -m pytest` with 935 tests" in release_notes
    assert "Scenarios `076` through `078`" in release_notes
    assert "from `001` through `078`" in release_notes
    assert "by_policy_id" in specification
    assert "by_lane_signature" in specification
    assert 'metadata["registry_hub"]' in specification
    assert "encryption_policy_history_mutated" in specification
    assert "Python 3.11 through 3.14" in roadmap
    assert "docs/RETAINED_AUDIT_ENCRYPTION_POLICY_v1_9.md" in readme
    assert "immutable v1.9.0 source snapshot" in checklist
    assert "pytest passes with 935 tests" in checklist
    assert "## [1.9.0] - 2026-07-26" in changelog

    for caveat in V1_9_RELEASE_SNAPSHOT_CAVEATS:
        assert caveat in combined_docs_normalized


def test_v1_9_python_and_ci_release_contract():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    ci = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    wheel_job = ci.split("  wheel-smoke:\n", maxsplit=1)[1]

    assert project["requires-python"] == ">=3.11"
    for version in ("3.11", "3.12", "3.13", "3.14"):
        assert f"Programming Language :: Python :: {version}" in project["classifiers"]
        assert f'"{version}"' in ci

    assert 'darwin-sim 1.9.0' in ci
    assert "python -m darwin.cli.main scenario-index" in ci
    assert "diff -u docs/SCENARIO_INDEX.md /tmp/generated_scenario_index.md" in ci
    assert "  wheel-smoke:\n" in ci
    assert 'python-version: "3.11"' in wheel_job
    assert "python -m build --wheel --outdir wheelhouse" in wheel_job
    assert "python -m pip install --force-reinstall wheelhouse/*.whl" in wheel_job
    assert "upload" not in wheel_job.lower()


def test_checked_in_scenarios_are_contiguous_through_078():
    scenario_numbers = sorted(
        path.name[:3]
        for path in (PROJECT_ROOT / "scenarios").glob("*.yaml")
        if path.name[:3].isdigit()
    )

    assert scenario_numbers == [f"{number:03}" for number in range(1, 79)]


def test_license_consistency():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    license_text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")

    assert project["license"] == "MIT"
    assert "License :: OSI Approved :: MIT License" in project["classifiers"]
    assert "## License\n\nMIT. See `LICENSE`." in readme
    assert license_text.startswith("MIT License\n\nCopyright (c) 2026 David Giles")
