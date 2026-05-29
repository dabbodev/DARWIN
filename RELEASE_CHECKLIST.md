# DARWIN v0.1 Release Checklist

- [ ] Tests pass with `python -m pytest`.
- [ ] Ruff passes with `python -m ruff check .`.
- [ ] CI workflow passes on push or pull request.
- [ ] README quick-start commands have been checked against the repo.
- [ ] Scenario listing and validation works with `python -m darwin.cli.main list-scenarios`.
- [ ] Basic scenario validates with `python -m darwin.cli.main validate-scenario scenarios/001_basic_registration.yaml`.
- [ ] Example scenario runs with `python -m darwin.cli.main run scenarios/001_basic_registration.yaml`.
- [ ] Golden scenario regression suite passes with `python scripts/run_all_scenarios.py`.
- [ ] Demo guide and CHANGELOG are up to date.
- [ ] Architecture overview and release notes are present in `docs/`.
- [ ] v0.2 roadmap is present in `docs/`.
- [ ] Package version is confirmed as `0.1.0`.
- [ ] Console script entry point `darwin-sim` is configured and usable.
- [ ] No real cryptography, authentication, or networking claims are made.
- [ ] Known limitations are listed in the README.

## Final Readiness Audit

- [ ] README repo-relative doc and scenario references point to existing files.
- [ ] `darwin.__version__`, `pyproject.toml`, CHANGELOG, and release notes all agree on `0.1.0`.
- [ ] CI checks match the local release verification commands.
- [ ] All checked-in YAML scenarios validate and run.
- [ ] Release notes clearly state v0.1 limitations and non-goals.
