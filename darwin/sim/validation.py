"""Lightweight scenario DSL validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.models.route import (
    CONGESTION_PENALTIES,
    STABILITY_PENALTIES,
    TRUST_PENALTIES,
)


class ValidationIssue(str):
    """Structured validation issue that remains string-compatible."""

    location: str
    message: str
    suggestion: str | None

    def __new__(
        cls,
        message: str,
        *,
        location: str = "",
        suggestion: str | None = None,
    ) -> ValidationIssue:
        obj = str.__new__(cls, message)
        obj.location = location
        obj.message = message
        obj.suggestion = suggestion
        return obj

    def to_dict(self) -> dict[str, str]:
        data = {
            "location": self.location,
            "message": self.message,
        }
        if self.suggestion:
            data["suggestion"] = self.suggestion
        return data

    def render(self) -> str:
        if self.suggestion:
            return f"{self.location}: {self.message} ({self.suggestion})"
        if self.location:
            return f"{self.location}: {self.message}"
        return self.message


@dataclass(frozen=True, slots=True)
class ScenarioValidationResult:
    """Result from lightweight scenario structure validation."""

    valid: bool
    errors: tuple[ValidationIssue, ...] = ()
    warnings: tuple[ValidationIssue, ...] = ()
    scenario_id: str | None = None
    name: str | None = None
    path: str | None = None

    @property
    def passed(self) -> bool:
        """Compatibility alias used by the v0.1 CLI and tests."""
        return self.valid

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "scenario_id": self.scenario_id,
            "valid": self.valid,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
        }


SUPPORTED_SETUP_SECTIONS = {
    "registry_hubs": ("hub_id", "scope_path"),
    "traffic_hubs": ("hub_id",),
    "hybrid_hubs": ("hub_id", "scope_path"),
    "links": ("from", "to"),
    "devices": ("device_id",),
}


STEP_REQUIRED_FIELDS = {
    "register_device": ("device", "registry_hub"),
    "resolve_label": ("registry_hub", "label"),
    "open_lane": ("source", "target", "traffic_hub"),
    "send_lane_data": ("traffic_hub", "lane", "payload"),
    "record_checkpoint": ("device", "registry_hub", "state"),
    "mark_in_transit": ("device", "registry_hub"),
    "pause_lanes_for_relocation": ("traffic_hub", "device"),
    "expire_relocation_hold": ("traffic_hub", "device"),
    "move_device": (
        "device",
        "old_registry_hub",
        "new_registry_hub",
        "old_traffic_hub",
        "new_traffic_hub",
    ),
    "create_invalid_move_contract": (
        "device",
        "old_registry_hub",
        "new_registry_hub",
        "old_traffic_hub",
        "new_traffic_hub",
    ),
    "simulate_duplicate_device_claim": ("registry_hub", "device", "claiming_attachment"),
    "resume_lanes_after_relocation": ("traffic_hub", "device"),
    "attempt_lane_send": ("traffic_hub", "lane", "payload"),
    "verify_rolling_proof": ("registry_hub", "device", "proof_valid"),
    "create_local_session": ("registry_hub", "device", "session_id", "auth_secret"),
    "rotate_local_session": ("registry_hub", "session_id", "new_auth_secret"),
    "expire_local_sessions": ("registry_hub", "current_time"),
    "verify_hmac_session_proof": (
        "registry_hub",
        "session_id",
        "counter",
        "nonce",
        "requested_capability",
    ),
    "record_cross_tree_packet": ("traffic_hub", "from_branch", "to_branch"),
    "recommend_traffic_bridge": ("traffic_hub",),
    "advance_time": (),
}


ASSERTION_REQUIRED_FIELDS = {
    "device_registered": ("registry_hub", "device"),
    "label_maps_to": ("registry_hub", "label", "device"),
    "device_state": ("registry_hub", "device", "expected"),
    "lane_state": ("traffic_hub", "lane", "expected"),
    "lane_not_active": ("traffic_hub", "lane"),
    "lane_sequence": ("traffic_hub", "lane", "last_sent", "last_acknowledged"),
    "flow_control_exists": ("traffic_hub", "lane"),
    "flow_control_absent": ("traffic_hub", "lane"),
    "latest_step_status": ("expected",),
    "relocation_failed": ("traffic_hub", "device"),
    "move_not_recorded": ("registry_hub", "device"),
    "attachment_is": ("registry_hub", "device", "expected_attachment"),
    "event_seen": ("event_type",),
    "conflict_exists": ("registry_hub", "conflict_type"),
    "quarantine_exists": ("registry_hub", "device"),
    "recommendation_exists": ("traffic_hub", "recommendation_type"),
    "route_for_lane": ("traffic_hub", "lane", "expected_route"),
    "session_state": ("registry_hub", "session_id", "expected"),
    "session_counter": ("registry_hub", "session_id", "expected"),
}


SUPPORTED_SCENARIO_CATEGORIES = {
    "registry",
    "traffic",
    "lane",
    "relocation",
    "security",
    "metrics",
    "preset",
    "visualization",
}

SUPPORTED_AUTH_MODES = {
    AUTH_MODE_SYMBOLIC,
    AUTH_MODE_HMAC_SHA256_EXPERIMENTAL,
}


def validate_scenario_data(
    data: dict[str, Any],
    *,
    path: str | None = None,
) -> ScenarioValidationResult:
    """Validate the scenario shape without running scenario steps."""
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    if not isinstance(data, dict):
        return ScenarioValidationResult(
            valid=False,
            errors=(
                _issue("$", "Scenario must be a mapping"),
            ),
            path=path,
        )

    scenario_id = data.get("scenario_id") or data.get("id")
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        errors.append(
            _issue(
                "scenario_id",
                "Scenario requires a non-empty scenario_id",
                suggestion="Add scenario_id at the top level.",
            )
        )
        scenario_id = None
    else:
        scenario_id = scenario_id.strip()

    raw_name = data.get("name")
    if isinstance(raw_name, str) and raw_name.strip():
        name = raw_name.strip()
    elif scenario_id is not None:
        name = _infer_name(scenario_id)
        warnings.append(
            _issue(
                "name",
                f"Scenario name missing; inferred {name!r}",
                suggestion="Add a name field for clearer CLI output.",
            )
        )
    else:
        name = None

    _validate_metadata(data, errors, warnings)
    _validate_setup(data, errors)
    _validate_steps(data, errors)
    _validate_assertions(data, errors)

    return ScenarioValidationResult(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        scenario_id=scenario_id,
        name=name,
        path=path,
    )


def _validate_metadata(
    data: dict[str, Any],
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> None:
    _validate_optional_text(data, "category", errors)
    _validate_optional_text(data, "description", errors)
    _validate_optional_text(data, "expected_result", errors)
    _validate_optional_string_list(data, "tags", errors)
    _validate_optional_string_list(data, "demonstrates", errors)

    category = data.get("category")
    if isinstance(category, str) and category.strip():
        normalized = category.strip()
        if normalized not in SUPPORTED_SCENARIO_CATEGORIES:
            warnings.append(
                _issue(
                    "category",
                    f"Unknown scenario category: {normalized}",
                    suggestion=(
                        "Use one of: "
                        + ", ".join(sorted(SUPPORTED_SCENARIO_CATEGORIES))
                    ),
                )
            )


def _validate_optional_text(
    data: dict[str, Any],
    field_name: str,
    errors: list[ValidationIssue],
) -> None:
    value = data.get(field_name)
    if value is not None and not isinstance(value, str):
        errors.append(_issue(field_name, f"Scenario {field_name} must be a string"))


def _validate_optional_string_list(
    data: dict[str, Any],
    field_name: str,
    errors: list[ValidationIssue],
) -> None:
    value = data.get(field_name)
    if value is None:
        return
    if not isinstance(value, list):
        errors.append(_issue(field_name, f"Scenario {field_name} must be a list"))
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(
                _issue(
                    f"{field_name}[{index}]",
                    f"Scenario {field_name} entries must be strings",
                )
            )


def _validate_setup(data: dict[str, Any], errors: list[ValidationIssue]) -> None:
    if "setup" not in data:
        errors.append(
            _issue(
                "setup",
                "Scenario requires setup",
                suggestion="Add setup: {} if no hubs or devices are needed.",
            )
        )
        return

    setup = data["setup"]
    if not isinstance(setup, dict):
        errors.append(_issue("setup", "Scenario setup must be a mapping"))
        return

    for section_name, section_value in setup.items():
        required_fields = SUPPORTED_SETUP_SECTIONS.get(section_name)
        if required_fields is None:
            errors.append(
                _issue(
                    f"setup.{section_name}",
                    f"Unknown setup section: {section_name}",
                    suggestion=(
                        "Use one of: "
                        + ", ".join(sorted(SUPPORTED_SETUP_SECTIONS))
                    ),
                )
            )
            continue

        for item_location, item in _iter_setup_items(section_name, section_value, errors):
            if not isinstance(item, dict):
                errors.append(_issue(item_location, "Setup item must be a mapping"))
                continue
            for field_name in required_fields:
                if field_name not in item:
                    errors.append(
                        _issue(
                            f"{item_location}.{field_name}",
                            f"Missing required setup field: {field_name}",
                        )
                    )
            if section_name == "links":
                _validate_link_metrics(item_location, item, errors)


def _iter_setup_items(
    section_name: str,
    section_value: Any,
    errors: list[ValidationIssue],
) -> list[tuple[str, dict[str, Any]]]:
    if section_value is None:
        return []
    if isinstance(section_value, list):
        return [
            (f"setup.{section_name}[{index}]", item)
            for index, item in enumerate(section_value)
        ]
    if isinstance(section_value, dict):
        key_field = SUPPORTED_SETUP_SECTIONS[section_name][0]
        items = []
        for key, raw_item in section_value.items():
            item = dict(raw_item) if isinstance(raw_item, dict) else raw_item
            if isinstance(item, dict):
                item.setdefault(key_field, key)
            items.append((f"setup.{section_name}.{key}", item))
        return items

    errors.append(
        _issue(
            f"setup.{section_name}",
            "Setup section must be a list or mapping",
        )
    )
    return []


def _validate_steps(data: dict[str, Any], errors: list[ValidationIssue]) -> None:
    steps = data.get("steps")
    if not isinstance(steps, list):
        errors.append(_issue("steps", "Scenario steps must be a list"))
        return

    for index, step in enumerate(steps):
        location = f"steps[{index}]"
        if not isinstance(step, dict):
            errors.append(_issue(location, "Scenario step must be a mapping"))
            continue

        action = step.get("action")
        if not isinstance(action, str) or not action.strip():
            errors.append(
                _issue(
                    f"{location}.action",
                    f"Scenario step {index + 1} requires a non-empty action",
                    suggestion="Add an action field such as register_device.",
                )
            )
            continue

        action = action.strip()
        required_fields = STEP_REQUIRED_FIELDS.get(action)
        if required_fields is None:
            errors.append(
                _issue(
                    f"{location}.action",
                    f"Unknown scenario step action: {action}",
                    suggestion="Use one of: " + ", ".join(sorted(STEP_REQUIRED_FIELDS)),
                )
            )
            continue

        _validate_required_fields(step, required_fields, location, "step", errors)
        _validate_step_auth_fields(step, location, errors)


def _validate_assertions(data: dict[str, Any], errors: list[ValidationIssue]) -> None:
    assertions = data.get("assertions")
    if not isinstance(assertions, list):
        errors.append(_issue("assertions", "Scenario assertions must be a list"))
        return

    for index, assertion in enumerate(assertions):
        location = f"assertions[{index}]"
        if not isinstance(assertion, dict):
            errors.append(_issue(location, "Scenario assertion must be a mapping"))
            continue

        assertion_type = assertion.get("type") or assertion.get("assert")
        if not isinstance(assertion_type, str) or not assertion_type.strip():
            errors.append(
                _issue(
                    f"{location}.type",
                    f"Scenario assertion {index + 1} requires a non-empty type",
                    suggestion="Add a type field such as event_seen.",
                )
            )
            continue

        assertion_type = assertion_type.strip()
        required_fields = ASSERTION_REQUIRED_FIELDS.get(assertion_type)
        if required_fields is None:
            errors.append(
                _issue(
                    f"{location}.type",
                    f"Unknown assertion type: {assertion_type}",
                    suggestion=(
                        "Use one of: "
                        + ", ".join(sorted(ASSERTION_REQUIRED_FIELDS))
                    ),
                )
            )
            continue

        _validate_required_fields(
            assertion,
            required_fields,
            location,
            "assertion",
            errors,
        )


def _validate_required_fields(
    item: dict[str, Any],
    required_fields: tuple[str, ...],
    location: str,
    item_name: str,
    errors: list[ValidationIssue],
) -> None:
    for field_name in required_fields:
        if field_name not in item:
            errors.append(
                _issue(
                    f"{location}.{field_name}",
                    f"Missing required {item_name} field: {field_name}",
                    suggestion=f"Add {field_name} to {location}.",
                )
            )


def _validate_step_auth_fields(
    step: dict[str, Any],
    location: str,
    errors: list[ValidationIssue],
) -> None:
    auth_mode = step.get("auth_mode")
    if auth_mode is not None and str(auth_mode) not in SUPPORTED_AUTH_MODES:
        errors.append(
            _issue(
                f"{location}.auth_mode",
                f"Unsupported auth_mode: {auth_mode}",
                suggestion="Use one of: " + ", ".join(sorted(SUPPORTED_AUTH_MODES)),
            )
        )

    auth_secret = step.get("auth_secret")
    if auth_secret is not None and not isinstance(auth_secret, str):
        errors.append(_issue(f"{location}.auth_secret", "auth_secret must be a string"))

    auth_tag = step.get("auth_tag")
    if auth_tag is not None and not isinstance(auth_tag, str):
        errors.append(_issue(f"{location}.auth_tag", "auth_tag must be a string"))

    _validate_optional_bool(step, "auth_tag_valid", location, errors)
    _validate_optional_bool(step, "tamper_auth_tag", location, errors)
    _validate_optional_bool(step, "tamper_payload_after_tag", location, errors)
    _validate_optional_bool(step, "tamper_counter", location, errors)
    _validate_optional_bool(step, "tamper_nonce", location, errors)
    _validate_optional_bool(step, "tamper_secret", location, errors)


def _validate_optional_bool(
    item: dict[str, Any],
    field_name: str,
    location: str,
    errors: list[ValidationIssue],
) -> None:
    value = item.get(field_name)
    if value is not None and not isinstance(value, bool):
        errors.append(_issue(f"{location}.{field_name}", f"{field_name} must be a boolean"))


def _validate_link_metrics(
    location: str,
    link: dict[str, Any],
    errors: list[ValidationIssue],
) -> None:
    latency_ms = link.get("latency_ms")
    if latency_ms is not None:
        try:
            parsed_latency = int(latency_ms)
        except (TypeError, ValueError):
            errors.append(_issue(f"{location}.latency_ms", "latency_ms must be an integer"))
        else:
            if parsed_latency < 0:
                errors.append(
                    _issue(f"{location}.latency_ms", "latency_ms must be non-negative")
                )

    _validate_enum(
        location,
        link,
        "congestion",
        tuple(CONGESTION_PENALTIES),
        errors,
    )
    _validate_enum(location, link, "trust", tuple(TRUST_PENALTIES), errors)
    _validate_enum(location, link, "stability", tuple(STABILITY_PENALTIES), errors)


def _validate_enum(
    location: str,
    item: dict[str, Any],
    field_name: str,
    supported_values: tuple[str, ...],
    errors: list[ValidationIssue],
) -> None:
    value = item.get(field_name)
    if value is None:
        return
    if str(value) not in supported_values:
        errors.append(
            _issue(
                f"{location}.{field_name}",
                f"Unsupported {field_name}: {value}",
                suggestion="Use one of: " + ", ".join(supported_values),
            )
        )


def _issue(
    location: str,
    message: str,
    *,
    suggestion: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(message, location=location, suggestion=suggestion)


def _infer_name(scenario_id: str) -> str:
    candidate = scenario_id
    if "_" in candidate:
        first, rest = candidate.split("_", 1)
        if first.isdigit() and rest:
            candidate = rest
    return candidate.replace("_", " ").strip().title() or scenario_id
