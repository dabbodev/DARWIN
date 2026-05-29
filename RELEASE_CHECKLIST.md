# DARWIN v0.1 Release Checklist

- [ ] Tests pass with `python -m pytest`.
- [ ] Ruff passes with `python -m ruff check .`.
- [ ] CI workflow passes on push or pull request.
- [ ] README quick-start commands have been checked against the repo.
- [ ] Scenario listing and validation works with `python -m darwin.cli.main list-scenarios`.
- [ ] Example scenario runs with `darwin-sim run scenarios/001_basic_registration.yaml`.
- [ ] Golden scenario regression suite passes with `python scripts/run_all_scenarios.py`.
- [ ] Demo guide and CHANGELOG are up to date.
- [ ] Package version is confirmed as `0.1.0`.
- [ ] Console script entry point `darwin-sim` is configured and usable.
- [ ] No real cryptography, authentication, or networking claims are made.
- [ ] Known limitations are listed in the README.
