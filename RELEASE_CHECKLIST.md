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

# DARWIN v0.2 Release Checklist

- [ ] Tests pass with `python -m pytest`.
- [ ] Ruff passes with `python -m ruff check .`.
- [ ] All checked-in scenarios pass with `python scripts/run_all_scenarios.py`.
- [ ] Scenario listing works with `python -m darwin.cli.main list-scenarios`.
- [ ] Preset listing works with `python -m darwin.cli.main list-presets`.
- [ ] Scenario index is generated with `python -m darwin.cli.main scenario-index`.
- [ ] Preset scenario runs, including `scenarios/011_preset_lane_demo.yaml`.
- [ ] Full JSON export sanity check is run for snapshot, events, and result output.
- [ ] Mermaid export is checked with a representative scenario.
- [ ] Timeline Markdown and JSON exports are checked with a representative scenario.
- [ ] README and v0.2 docs are updated.
- [ ] CHANGELOG includes the dated `0.2.0` section.
- [ ] Final release notes are updated in `docs/RELEASE_NOTES_v0_2.md`.
- [ ] Documentation avoids production networking, DNS, or production cryptography claims.
- [ ] Package versioning and final release tag decision are handled separately from this checklist.

## v0.2 Manual Validation Commands

```bash
python -m pytest
python -m ruff check .
python scripts/run_all_scenarios.py
python -m darwin.cli.main --version
python -m darwin.cli.main list-scenarios
python -m darwin.cli.main scenario-index
python -m darwin.cli.main list-presets
python -m darwin.cli.main describe-scenario scenarios/011_preset_lane_demo.yaml
python -m darwin.cli.main expand-scenario scenarios/011_preset_lane_demo.yaml
python -m darwin.cli.main run scenarios/004_relocation_pause_resume.yaml --export-snapshot tmp_v02_snapshot.json --export-events tmp_v02_events.json --export-result tmp_v02_result.json --export-mermaid tmp_v02.mmd --export-timeline-md tmp_v02_timeline.md --export-timeline-json tmp_v02_timeline.json
```
