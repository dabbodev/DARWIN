# DARWIN v0.1 Release Checklist

- [x] Tests pass with `python -m pytest`.
- [x] Ruff passes with `python -m ruff check .`.
- [x] CI workflow passes on push or pull request.
- [x] README quick-start commands have been checked against the repo.
- [x] Scenario listing and validation works with `python -m darwin.cli.main list-scenarios`.
- [x] Basic scenario validates with `python -m darwin.cli.main validate-scenario scenarios/001_basic_registration.yaml`.
- [x] Example scenario runs with `python -m darwin.cli.main run scenarios/001_basic_registration.yaml`.
- [x] Golden scenario regression suite passes with `python scripts/run_all_scenarios.py`.
- [x] Demo guide and CHANGELOG are up to date.
- [x] Architecture overview and release notes are present in `docs/`.
- [x] v0.2 roadmap is present in `docs/`.
- [x] Package version is confirmed as `0.1.0`.
- [x] Project metadata, README, and root `LICENSE` all identify the license as MIT.
- [x] Console script entry point `darwin-sim` is configured and usable.
- [x] No real cryptography, authentication, or networking claims are made.
- [x] Known limitations are listed in the README.

## Final Readiness Audit

- [x] README repo-relative doc and scenario references point to existing files.
- [x] `darwin.__version__`, `pyproject.toml`, CHANGELOG, and release notes all agree on `0.1.0`.
- [x] CI checks match the local release verification commands.
- [x] All checked-in YAML scenarios validate and run.
- [x] Release notes clearly state v0.1 limitations and non-goals.
