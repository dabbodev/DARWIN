import re
import tomllib
from pathlib import Path

import darwin

PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
        PROJECT_ROOT / "docs" / "RELEASE_NOTES_v0_8_DRAFT.md"
    ).read_text(encoding="utf-8")

    assert darwin.__version__ == project_version
    assert f"[{project_version}]" in changelog or f"## v{project_version}" in changelog
    assert f"v{project_version}" in current_release_notes
    assert "v0.1.0" in release_notes


def test_license_consistency():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    license_text = (PROJECT_ROOT / "LICENSE").read_text(encoding="utf-8")

    assert project["license"] == "MIT"
    assert "License :: OSI Approved :: MIT License" in project["classifiers"]
    assert "## License\n\nMIT. See `LICENSE`." in readme
    assert license_text.startswith("MIT License\n\nCopyright (c) 2026 David Giles")
