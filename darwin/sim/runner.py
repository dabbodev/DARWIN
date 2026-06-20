"""Deterministic scenario runner for DARWIN v0.1."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from darwin.auth.hmac_bridge import (
    checkpoint_auth_material,
    compute_hmac_tag,
    rolling_proof_material,
)
from darwin.auth.modes import AUTH_MODE_HMAC_SHA256_EXPERIMENTAL, AUTH_MODE_SYMBOLIC
from darwin.auth.move_contract import attach_move_auth
from darwin.models.adapter_endpoint import AdapterEndpoint
from darwin.models.checkpoint import make_checkpoint_packet
from darwin.models.device import Device
from darwin.models.encrypted_delivery import (
    EncryptedDeliveryRequest,
    make_plaintext_delivery_request,
    make_symbolic_encrypted_delivery_request,
)
from darwin.models.encryption import (
    DEFAULT_ENCRYPTION_PROFILE,
    DEFAULT_SYMBOLIC_ENVELOPE_ALGORITHM_REF,
    EncryptedEnvelopeMetadata,
    EncryptionIdentity,
    EncryptionPolicyDecision,
    KeyBundleReference,
    MailboxEncryptionBinding,
    MailboxEncryptionPolicy,
)
from darwin.models.hub import LocalDeviceRecord
from darwin.models.lane_signature import (
    LaneDefinition,
    LaneDeliveryFallbackPolicy,
    make_basic_messaging_lane_definition,
)
from darwin.models.mailbox import MailboxCapability, MailboxIdentity, format_mailbox_address
from darwin.models.message import MessageEnvelope
from darwin.models.route import LinkMetrics
from darwin.models.stream_offer import (
    RendezvousPollResult,
    RendezvousRequest,
    StreamOffer,
    make_lane_admission_policy,
    make_rendezvous_request,
    make_stream_offer,
)
from darwin.registry.adapter_endpoints import (
    register_adapter_endpoint as register_adapter_endpoint_op,
)
from darwin.registry.alias_authority import (
    claim_alias_through_authority_chain as claim_alias_through_authority_chain_op,
)
from darwin.registry.aliases import (
    claim_alias as claim_alias_op,
)
from darwin.registry.aliases import (
    claim_bundle_alias as claim_bundle_alias_op,
)
from darwin.registry.aliases import (
    claim_progressive_alias as claim_progressive_alias_op,
)
from darwin.registry.aliases import (
    create_alias_bundle as create_alias_bundle_op,
)
from darwin.registry.aliases import (
    release_alias as release_alias_op,
)
from darwin.registry.aliases import (
    resolve_alias as resolve_alias_op,
)
from darwin.registry.checkpoints import record_checkpoint as record_checkpoint_op
from darwin.registry.encrypted_delivery import (
    evaluate_encrypted_delivery_request as evaluate_encrypted_delivery_request_op,
)
from darwin.registry.encrypted_delivery import (
    summarize_encrypted_delivery_result,
)
from darwin.registry.encryption_registry import (
    evaluate_registered_mailbox_encryption_policy as evaluate_registered_policy_op,
)
from darwin.registry.encryption_registry import (
    register_encryption_identity as register_encryption_identity_op,
)
from darwin.registry.encryption_registry import (
    register_key_bundle_reference as register_key_bundle_reference_op,
)
from darwin.registry.encryption_registry import (
    register_mailbox_encryption_binding as register_mailbox_encryption_binding_op,
)
from darwin.registry.encryption_registry import (
    register_mailbox_encryption_policy as register_mailbox_encryption_policy_op,
)
from darwin.registry.lane_registry import (
    register_lane_definition as register_lane_definition_op,
)
from darwin.registry.mailbox_registry import (
    bind_mailbox_capability as bind_mailbox_capability_op,
)
from darwin.registry.mailbox_registry import (
    register_mailbox as register_mailbox_op,
)
from darwin.registry.message_delivery import (
    deliver_message_to_mailbox as deliver_message_to_mailbox_op,
)
from darwin.registry.operations import (
    register_device as register_device_op,
)
from darwin.registry.operations import (
    resolve_label as resolve_label_op,
)
from darwin.registry.relocation import (
    create_move_contract,
    update_attachment_after_move,
)
from darwin.registry.relocation import (
    mark_in_transit as mark_in_transit_op,
)
from darwin.registry.security import (
    detect_duplicate_device_claim as detect_duplicate_device_claim_op,
)
from darwin.registry.security import revoke_device as revoke_device_op
from darwin.registry.security import verify_rolling_proof as verify_rolling_proof_op
from darwin.registry.sessions import (
    create_local_session as create_local_session_op,
)
from darwin.registry.sessions import (
    expire_local_sessions as expire_local_sessions_op,
)
from darwin.registry.sessions import (
    get_local_session,
)
from darwin.registry.sessions import (
    revoke_device_sessions as revoke_device_sessions_op,
)
from darwin.registry.sessions import (
    revoke_local_session as revoke_local_session_op,
)
from darwin.registry.sessions import (
    rotate_local_session as rotate_local_session_op,
)
from darwin.registry.sessions import (
    verify_hmac_rolling_proof_for_session as verify_hmac_session_proof_op,
)
from darwin.registry.stream_offers import (
    evaluate_lane_admission_policy as evaluate_lane_admission_policy_op,
)
from darwin.registry.stream_offers import (
    get_held_stream_offer as get_held_stream_offer_op,
)
from darwin.registry.stream_offers import (
    hold_stream_offer as hold_stream_offer_op,
)
from darwin.registry.stream_offers import (
    mark_stream_offers_discoverable as mark_stream_offers_discoverable_op,
)
from darwin.registry.stream_offers import (
    poll_held_stream_offers as poll_held_stream_offers_op,
)
from darwin.registry.stream_offers import (
    record_lane_admission_decision as record_lane_admission_decision_op,
)
from darwin.registry.stream_offers import (
    record_rendezvous_poll_result as record_rendezvous_poll_result_op,
)
from darwin.sim.assertions import AssertionResult, evaluate_assertions
from darwin.sim.scenarios import Scenario, load_scenario
from darwin.sim.world import World
from darwin.traffic.lanes import open_lane as open_lane_op
from darwin.traffic.lanes import send_lane_data as send_lane_data_op
from darwin.traffic.metrics import (
    recommend_traffic_bridge as recommend_traffic_bridge_op,
)
from darwin.traffic.metrics import (
    record_cross_tree_packet as record_cross_tree_packet_op,
)
from darwin.traffic.relocation import (
    expire_relocation_hold as expire_relocation_hold_op,
)
from darwin.traffic.relocation import (
    pause_lanes_for_relocation as pause_lanes_for_relocation_op,
)
from darwin.traffic.relocation import (
    resume_lanes_after_relocation as resume_lanes_after_relocation_op,
)


@dataclass(slots=True)
class ScenarioRunResult:
    scenario_id: str
    passed: bool
    assertion_results: list[AssertionResult]
    event_log: list[str]
    final_snapshot: dict[str, object]
    world: World

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "assertion_results": [
                asdict(assertion_result)
                for assertion_result in self.assertion_results
            ],
            "event_log": list(self.event_log),
            "final_snapshot": self.final_snapshot,
        }

    def render(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines = [f"{self.scenario_id}: {status}", "", "Event log:"]
        lines.extend(self.event_log or ["(no events)"])
        lines.extend(["", "Final snapshot:", json.dumps(self.final_snapshot, indent=2)])
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()


def run_scenario(source: Scenario | dict[str, Any] | str | Path) -> ScenarioRunResult:
    """Run a scenario from a dict or file path and return deterministic results."""
    scenario = load_scenario(source)
    world = World()
    _apply_setup(world, scenario.setup)

    for step in scenario.steps:
        _run_step(world, step.action, step.fields)
        world.advance_time()

    assertion_results = evaluate_assertions(world, scenario.assertions)
    passed = all(result.passed for result in assertion_results)
    return ScenarioRunResult(
        scenario_id=scenario.scenario_id,
        passed=passed,
        assertion_results=assertion_results,
        event_log=world.event_log.lines,
        final_snapshot=world.snapshot(detailed=True),
        world=world,
    )


def run_scenario_dict(data: dict[str, Any]) -> ScenarioRunResult:
    return run_scenario(data)


def _apply_setup(world: World, setup: dict[str, Any]) -> None:
    for hub_config in _configs(setup.get("registry_hubs", []), "hub_id"):
        world.create_registry_hub(
            hub_id=str(hub_config["hub_id"]),
            scope_path=str(hub_config["scope_path"]),
            parent_hub_id=_optional_str(hub_config.get("parent_hub_id")),
            alias_authority_policy=_optional_policy(
                hub_config.get("alias_authority_policy")
            ),
        )

    for hub_config in _configs(setup.get("traffic_hubs", []), "hub_id"):
        world.create_traffic_hub(hub_id=str(hub_config["hub_id"]))

    for hub_config in _configs(setup.get("hybrid_hubs", []), "hub_id"):
        world.create_hybrid_hub(
            hub_id=str(hub_config["hub_id"]),
            scope_path=str(hub_config["scope_path"]),
            parent_hub_id=_optional_str(hub_config.get("parent_hub_id")),
            alias_authority_policy=_optional_policy(
                hub_config.get("alias_authority_policy")
            ),
        )

    for link_config in _configs(setup.get("links", []), "from"):
        world.connect_traffic_hubs(
            str(link_config["from"]),
            str(link_config["to"]),
            _link_metrics(link_config),
        )

    for device_config in _configs(setup.get("devices", []), "device_id"):
        device = Device(
            device_id=str(device_config["device_id"]),
            label=str(device_config.get("label", device_config["device_id"])),
            checkpoint_tier=int(device_config.get("checkpoint_tier", 1)),
        )
        world.add_device(device)

        registry_hub_id = device_config.get("registry_hub")
        if registry_hub_id is not None:
            register_device_op(
                world.registry_hubs[str(registry_hub_id)],
                device,
                requested_label=device.label,
                checkpoint_tier=device.checkpoint_tier,
                current_time=world.current_time,
            )

        traffic_hub_id = device_config.get("traffic_hub")
        if traffic_hub_id is not None:
            world.attach_device_to_traffic(device.device_id, str(traffic_hub_id))


def _run_step(world: World, action: str, fields: dict[str, Any]) -> None:
    handlers = {
        "register_device": _step_register_device,
        "resolve_label": _step_resolve_label,
        "claim_alias": _step_claim_alias,
        "create_alias_bundle": _step_create_alias_bundle,
        "claim_bundle_alias": _step_claim_bundle_alias,
        "claim_progressive_alias": _step_claim_progressive_alias,
        "claim_alias_through_authority_chain": (
            _step_claim_alias_through_authority_chain
        ),
        "resolve_alias": _step_resolve_alias,
        "release_alias": _step_release_alias,
        "open_lane": _step_open_lane,
        "send_lane_data": _step_send_lane_data,
        "record_checkpoint": _step_record_checkpoint,
        "mark_in_transit": _step_mark_in_transit,
        "pause_lanes_for_relocation": _step_pause_lanes_for_relocation,
        "expire_relocation_hold": _step_expire_relocation_hold,
        "move_device": _step_move_device,
        "create_invalid_move_contract": _step_create_invalid_move_contract,
        "simulate_duplicate_device_claim": _step_simulate_duplicate_device_claim,
        "resume_lanes_after_relocation": _step_resume_lanes_after_relocation,
        "attempt_lane_send": _step_send_lane_data,
        "verify_rolling_proof": _step_verify_rolling_proof,
        "create_local_session": _step_create_local_session,
        "rotate_local_session": _step_rotate_local_session,
        "revoke_local_session": _step_revoke_local_session,
        "revoke_device_sessions": _step_revoke_device_sessions,
        "revoke_device": _step_revoke_device,
        "expire_local_sessions": _step_expire_local_sessions,
        "verify_hmac_session_proof": _step_verify_hmac_session_proof,
        "record_cross_tree_packet": _step_record_cross_tree_packet,
        "recommend_traffic_bridge": _step_recommend_traffic_bridge,
        "register_lane_definition": _step_register_lane_definition,
        "register_mailbox": _step_register_mailbox,
        "bind_mailbox_capability": _step_bind_mailbox_capability,
        "register_adapter_endpoint": _step_register_adapter_endpoint,
        "deliver_message": _step_deliver_message,
        "evaluate_encrypted_delivery_request": _step_evaluate_encrypted_delivery_request,
        "register_encryption_identity": _step_register_encryption_identity,
        "register_key_bundle_reference": _step_register_key_bundle_reference,
        "register_mailbox_encryption_binding": (
            _step_register_mailbox_encryption_binding
        ),
        "register_mailbox_encryption_policy": _step_register_mailbox_encryption_policy,
        "evaluate_mailbox_encryption_policy": _step_evaluate_mailbox_encryption_policy,
        "hold_stream_offer": _step_hold_stream_offer,
        "poll_held_stream_offers": _step_poll_held_stream_offers,
        "mark_stream_offers_discoverable": _step_mark_stream_offers_discoverable,
        "evaluate_lane_admission_policy": _step_evaluate_lane_admission_policy,
        "advance_time": _step_advance_time,
    }
    try:
        handler = handlers[action]
    except KeyError as exc:
        raise ValueError(f"Unsupported scenario step action: {action}") from exc
    handler(world, fields)


def _step_register_device(world: World, fields: dict[str, Any]) -> None:
    device_id = str(fields["device"])
    label = str(fields.get("label", device_id))
    device = world.devices.get(device_id)
    if device is None:
        device = Device(device_id=device_id, label=label)
        world.add_device(device)

    hub = world.registry_hubs[str(fields["registry_hub"])]
    result = register_device_op(
        hub,
        device,
        requested_label=label,
        checkpoint_tier=device.checkpoint_tier,
        current_time=world.current_time,
    )
    world.action_results.append(result)

    if isinstance(result, LocalDeviceRecord):
        event_type = "label_conflict" if result.current_label != label else "registered_device"
        suffix = "" if result.current_label == label else f" (requested {label}; label_conflict)"
        world.log(
            f"registered {device_id} at {hub.hub_id} as {result.current_label}{suffix}",
            event_type=event_type,
            actor=device_id,
            target=hub.hub_id,
            device_id=device_id,
            hub_id=hub.hub_id,
            status=result.current_state,
            data={
                "requested_label": label,
                "assigned_label": result.current_label,
                "passport_id": result.passport_id,
            },
        )
        return

    world.log(
        f"registration failed for {device_id} at {hub.hub_id}: {result.reason}",
        event_type=result.action,
        actor=device_id,
        target=hub.hub_id,
        device_id=device_id,
        hub_id=hub.hub_id,
        status=result.action,
        data={"reason": result.reason},
    )


def _step_resolve_label(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    label = str(fields["label"])
    result = resolve_label_op(hub, label)
    world.action_results.append(result)
    if result is None:
        world.log(
            f"resolved {label} at {hub.hub_id}: not found",
            event_type="label_not_found",
            target=hub.hub_id,
            hub_id=hub.hub_id,
            status="not_found",
            data={"label": label},
        )
    else:
        world.log(
            f"resolved {label} at {hub.hub_id} to {result.device_id}",
            event_type="label_resolved",
            actor=hub.hub_id,
            target=result.device_id,
            device_id=result.device_id,
            hub_id=hub.hub_id,
            status="resolved",
            data={"label": label},
        )


def _step_claim_alias(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    alias = str(fields["alias"])
    target_device_id = str(fields["target_device"])
    result = claim_alias_op(
        hub,
        alias,
        target_device_id,
        requested_by_device_id=_optional_str(fields.get("requested_by_device")),
        alias_type=str(fields.get("alias_type", "device_alias")),
        visibility=str(fields.get("visibility", "local")),
        ttl=_optional_int(fields.get("ttl")),
    )
    world.action_results.append(result)
    event_type = "alias_claimed" if result.success else "alias_claim_failed"
    world.log(
        f"{event_type} {alias} at {hub.hub_id} for {target_device_id}",
        event_type=event_type,
        actor=_optional_str(fields.get("requested_by_device")) or target_device_id,
        target=target_device_id,
        device_id=target_device_id,
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "alias": alias,
            "target_device": target_device_id,
            "success": result.success,
            "reason": result.reason,
            "conflict_id": result.conflict_id,
        },
    )


def _step_create_alias_bundle(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    bundle_path = str(fields["bundle_path"])
    result = create_alias_bundle_op(
        hub,
        bundle_path,
        delegated_to_registry_hub=_optional_str(fields.get("delegated_to_registry_hub")),
        bundle_type=str(fields.get("bundle_type", "alias_zone")),
        visibility=str(fields.get("visibility", "local")),
        allowed_record_types=_optional_str_list(fields.get("allowed_record_types")),
        created_by_device_id=_optional_str(fields.get("created_by_device")),
    )
    world.action_results.append(result)
    event_type = "alias_bundle_created" if result.success else "alias_bundle_failed"
    world.log(
        f"{event_type} {bundle_path} at {hub.hub_id}",
        event_type=event_type,
        actor=_optional_str(fields.get("created_by_device")) or hub.hub_id,
        target=bundle_path,
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "bundle_path": bundle_path,
            "bundle_type": None if result.bundle is None else result.bundle.bundle_type,
            "delegated_to_registry_hub": (
                None
                if result.bundle is None
                else result.bundle.delegated_to_registry_hub
            ),
            "success": result.success,
            "reason": result.reason,
        },
    )


def _step_claim_bundle_alias(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    bundle_path = str(fields["bundle_path"])
    child_name = str(fields["child_name"])
    target_device_id = str(fields["target_device"])
    result = claim_bundle_alias_op(
        hub,
        bundle_path,
        child_name,
        target_device_id,
        requested_by_device_id=_optional_str(fields.get("requested_by_device")),
        alias_type=str(fields.get("alias_type", "device_alias")),
        visibility=str(fields.get("visibility", "local")),
        ttl=_optional_int(fields.get("ttl")),
    )
    world.action_results.append(result)
    alias = f"{bundle_path}.{child_name}"
    event_type = "bundle_alias_claimed" if result.success else "bundle_alias_failed"
    world.log(
        f"{event_type} {alias} at {hub.hub_id} for {target_device_id}",
        event_type=event_type,
        actor=_optional_str(fields.get("requested_by_device")) or target_device_id,
        target=target_device_id,
        device_id=target_device_id,
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "bundle_path": bundle_path,
            "child_name": child_name,
            "alias": alias,
            "target_device": target_device_id,
            "success": result.success,
            "reason": result.reason,
        },
    )


def _step_claim_progressive_alias(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    requested_alias = str(fields["requested_alias"])
    local_name = str(fields["local_name"])
    target_device_id = str(fields["target_device"])
    result = claim_progressive_alias_op(
        hub,
        requested_alias,
        local_name,
        target_device_id,
        requested_by_device_id=_optional_str(fields.get("requested_by_device")),
        fallback_allowed=bool(fields.get("fallback_allowed", True)),
        visibility=str(fields.get("visibility", "local")),
        ttl=_optional_int(fields.get("ttl")),
    )
    world.action_results.append(result)
    event_type = "progressive_alias_claimed" if result.success else "progressive_alias_failed"
    world.log(
        f"{event_type} {requested_alias} at {hub.hub_id} for {target_device_id}",
        event_type=event_type,
        actor=_optional_str(fields.get("requested_by_device")) or target_device_id,
        target=target_device_id,
        device_id=target_device_id,
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "requested_alias": requested_alias,
            "granted_alias": result.granted_alias,
            "local_name": local_name,
            "target_device": target_device_id,
            "success": result.success,
            "reason": result.reason,
            "fallback_reason": result.fallback_reason,
            "authority_ceiling": result.authority_ceiling,
            "conflict_id": result.conflict_id,
        },
    )


def _step_claim_alias_through_authority_chain(
    world: World,
    fields: dict[str, Any],
) -> None:
    start_hub_id = str(fields["registry_hub"])
    requested_alias = str(fields["requested_alias"])
    local_name = str(fields["local_name"])
    target_device_id = str(fields["target_device"])
    result = claim_alias_through_authority_chain_op(
        world.registry_hubs,
        start_hub_id,
        requested_alias,
        local_name,
        target_device_id,
        requested_by_device_id=_optional_str(fields.get("requested_by_device")),
        fallback_allowed=bool(fields.get("fallback_allowed", True)),
        visibility=str(fields.get("visibility", "local")),
        ttl=_optional_int(fields.get("ttl")),
    )
    world.action_results.append(result)
    event_type = (
        "alias_authority_chain_claimed"
        if result.success
        else "alias_authority_chain_failed"
    )
    authority_path = result.authority_path
    authority_summary = authority_path.to_summary()
    world.log(
        f"{event_type} {requested_alias} from {start_hub_id} for {target_device_id}",
        event_type=event_type,
        actor=_optional_str(fields.get("requested_by_device")) or target_device_id,
        target=target_device_id,
        device_id=target_device_id,
        hub_id=start_hub_id,
        status=result.status,
        data={
            "requested_alias": requested_alias,
            "granted_alias": result.granted_alias,
            "target_device": target_device_id,
            "success": result.success,
            "status": result.status,
            "reason": result.reason,
            "authority_ceiling": result.authority_ceiling,
            "authority_path_final_status": authority_summary.final_status,
            "decision_count": authority_summary.decision_count,
            "path_hubs": list(authority_summary.path_hubs),
            "decisions": [
                decision.to_dict() for decision in authority_path.decisions
            ],
        },
    )


def _step_resolve_alias(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    alias = str(fields["alias"])
    result = resolve_alias_op(hub, alias)
    world.action_results.append(result)
    event_type = "alias_resolved" if result.success else "alias_not_resolved"
    world.log(
        f"{event_type} {alias} at {hub.hub_id}",
        event_type=event_type,
        actor=hub.hub_id,
        target=result.target_device_id,
        device_id=result.target_device_id,
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "alias": alias,
            "target_device": result.target_device_id,
            "target_identity_chain": result.target_identity_chain,
            "success": result.success,
            "reason": result.reason,
        },
    )


def _step_release_alias(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    alias = str(fields["alias"])
    result = release_alias_op(
        hub,
        alias,
        requested_by_device_id=_optional_str(fields.get("requested_by_device")),
    )
    world.action_results.append(result)
    event_type = "alias_released" if result.success else "alias_release_failed"
    world.log(
        f"{event_type} {alias} at {hub.hub_id}",
        event_type=event_type,
        actor=_optional_str(fields.get("requested_by_device")),
        target=alias,
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "alias": alias,
            "success": result.success,
            "reason": result.reason,
        },
    )


def _step_open_lane(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    result = open_lane_op(
        hub,
        source_device_id=str(fields["source"]),
        target_device_id=str(fields["target"]),
        all_hubs=world.traffic_hubs,
        lane_id=_optional_str(fields.get("lane_id")),
    )
    world.action_results.append(result)
    if result.lane is not None:
        world.lanes[result.lane_id or result.lane.lane_id] = result.lane
    world.log(
        f"{result.action} {result.lane_id} from {result.source_device_id} "
        f"to {result.target_device_id} via {result.route}",
        event_type=result.action,
        actor=result.source_device_id,
        target=result.target_device_id,
        device_id=result.source_device_id,
        hub_id=hub.hub_id,
        lane_id=result.lane_id,
        status=result.action,
        data={
            "route": list(result.route),
            "next_hop": result.next_hop,
            "final_hub_id": result.final_hub_id,
            "route_status": result.route_status,
            "total_cost": result.total_cost,
            "cost_breakdown": result.cost_breakdown,
        },
    )


def _step_send_lane_data(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    result = send_lane_data_op(
        hub,
        lane_id=str(fields["lane"]),
        payload=fields.get("payload"),
        all_hubs=world.traffic_hubs,
        auth_tag_valid=bool(fields.get("auth_tag_valid", True)),
        auth_mode=str(fields.get("auth_mode", AUTH_MODE_SYMBOLIC)),
        auth_secret=_optional_str(fields.get("auth_secret")),
        tamper_auth_tag=bool(fields.get("tamper_auth_tag", False)),
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} on {result.lane_id} seq={result.sequence_number} "
        f"sent={result.last_sent_sequence} ack={result.last_acknowledged_sequence}",
        event_type=result.action,
        actor=result.source_device_id,
        target=result.target_device_id,
        device_id=result.source_device_id,
        hub_id=hub.hub_id,
        lane_id=result.lane_id,
        status=result.action,
        data={
            "packet_id": result.packet_id,
            "sequence_number": result.sequence_number,
            "last_sent_sequence": result.last_sent_sequence,
            "last_acknowledged_sequence": result.last_acknowledged_sequence,
            "route": list(result.route),
            "next_hop": result.next_hop,
            "final_hub_id": result.final_hub_id,
            "route_status": result.route_status,
            "total_cost": result.total_cost,
            "cost_breakdown": result.cost_breakdown,
        },
    )


def _step_record_checkpoint(world: World, fields: dict[str, Any]) -> None:
    device = world.devices[str(fields["device"])]
    hub = world.registry_hubs[str(fields["registry_hub"])]
    packet = make_checkpoint_packet(
        device,
        hub.hub_id,
        state=str(fields["state"]),
        current_time=world.current_time,
        auth_tag_valid=bool(fields.get("auth_tag_valid", True)),
        auth_mode=str(fields.get("auth_mode", AUTH_MODE_SYMBOLIC)),
        battery_level=_optional_int(fields.get("battery_level")),
        active_lane_count=_optional_int(fields.get("active_lane_count")),
    )
    auth_secret = _optional_str(fields.get("auth_secret"))
    if packet.auth_mode == AUTH_MODE_HMAC_SHA256_EXPERIMENTAL and auth_secret is not None:
        packet.auth_tag = compute_hmac_tag(auth_secret, checkpoint_auth_material(packet))
        if bool(fields.get("tamper_payload_after_tag", False)):
            packet.payload["device_state"] = f"tampered_{packet.state}"
        if bool(fields.get("tamper_auth_tag", False)) or not packet.auth_tag_valid:
            packet.auth_tag = _tampered_tag(packet.auth_tag)

    result = record_checkpoint_op(hub, packet, auth_secret=auth_secret)
    world.action_results.append(result)
    world.log(
        f"{result.action} for {result.device_id} at {hub.hub_id} state={fields['state']}",
        event_type=result.action,
        actor=result.device_id,
        target=hub.hub_id,
        device_id=result.device_id,
        hub_id=hub.hub_id,
        status=result.action,
        data={
            "state": fields["state"],
            "checkpoint_tier": device.checkpoint_tier,
            "reason": result.reason,
        },
    )


def _step_mark_in_transit(world: World, fields: dict[str, Any]) -> None:
    device_id = str(fields["device"])
    hub = world.registry_hubs[str(fields["registry_hub"])]
    result = mark_in_transit_op(hub, device_id, current_time=world.current_time)
    if device_id in world.devices and result.success:
        world.devices[device_id].mark_in_transit()
    world.action_results.append(result)
    world.log(
        f"{result.action} {device_id} at {hub.hub_id}",
        event_type=result.action,
        actor=device_id,
        target=hub.hub_id,
        device_id=device_id,
        hub_id=hub.hub_id,
        status="in_transit" if result.success else result.action,
        data={"reason": result.reason},
    )


def _step_pause_lanes_for_relocation(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    result = pause_lanes_for_relocation_op(hub, str(fields["device"]))
    world.action_results.append(result)
    world.log(
        f"{result.action} for {result.device_id}: {result.affected_lanes}",
        event_type=result.action,
        actor=result.device_id,
        target=hub.hub_id,
        device_id=result.device_id,
        hub_id=hub.hub_id,
        status=result.action,
        data={
            "affected_lanes": list(result.affected_lanes),
            "flow_control_lanes": [
                flow_control.lane_id for flow_control in result.flow_controls
            ],
            "relocation_state": (
                None if result.relocation is None else result.relocation.state
            ),
            "reason": result.reason,
        },
    )


def _step_expire_relocation_hold(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    current_time = _optional_int(fields.get("current_time"))
    result = expire_relocation_hold_op(
        hub,
        str(fields["device"]),
        current_time=world.current_time if current_time is None else current_time,
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} for {result.device_id}: {result.failed_lanes}",
        event_type=result.action,
        actor=result.device_id,
        target=hub.hub_id,
        device_id=result.device_id,
        hub_id=hub.hub_id,
        status=result.action,
        data={
            "failed_lanes": list(result.failed_lanes),
            "relocation_state": (
                None if result.relocation is None else result.relocation.state
            ),
            "reason": result.reason,
        },
    )


def _step_move_device(world: World, fields: dict[str, Any]) -> None:
    device_id = str(fields["device"])
    device = world.devices[device_id]
    old_registry_hub = world.registry_hubs[str(fields["old_registry_hub"])]
    new_registry_hub = world.registry_hubs[str(fields["new_registry_hub"])]
    old_traffic_hub = world.traffic_hubs[str(fields["old_traffic_hub"])]
    new_traffic_hub = world.traffic_hubs[str(fields["new_traffic_hub"])]
    new_scope = str(fields.get("new_scope", new_registry_hub.scope_path))

    old_record = old_registry_hub.devices.get(device_id)
    passport_id = (
        old_record.passport_id
        if old_record is not None
        else device.passport_id or f"passport_{device_id}"
    )
    contract = create_move_contract(
        device_id=device_id,
        passport_id=passport_id,
        from_scope=old_registry_hub.scope_path,
        to_scope=new_scope,
        old_attachment=old_registry_hub.hub_id,
        new_attachment=new_registry_hub.hub_id,
        timestamp=world.current_time,
    )
    auth_mode = str(fields.get("auth_mode", AUTH_MODE_SYMBOLIC))
    if auth_mode != AUTH_MODE_SYMBOLIC:
        contract.auth_mode = auth_mode

    if auth_mode == AUTH_MODE_HMAC_SHA256_EXPERIMENTAL:
        _attach_hmac_move_auth_from_step(contract, fields)
        _tamper_move_contract_from_step(contract, fields)

    result = update_attachment_after_move(
        old_registry_hub,
        device_id,
        new_attachment=contract.new_attachment,
        new_scope=contract.to_scope,
        move_contract=contract,
    )

    if result.success:
        old_traffic_hub.detach_device(device_id)
        new_traffic_hub.attach_device(device)
        device.current_registry_hub = new_registry_hub.hub_id
        device.current_traffic_hub = new_traffic_hub.hub_id
        device.state = "online"

        if new_registry_hub.hub_id != old_registry_hub.hub_id:
            register_device_op(
                new_registry_hub,
                device,
                requested_label=device.label,
                checkpoint_tier=device.checkpoint_tier,
                current_time=world.current_time,
            )

    world.action_results.append(result)
    event_type = "device_moved" if result.success else result.action
    status = "online" if result.success else result.action
    world.log(
        f"{event_type} {device_id} from {old_traffic_hub.hub_id} to {new_traffic_hub.hub_id}",
        event_type=event_type,
        actor=device_id,
        target=new_traffic_hub.hub_id,
        device_id=device_id,
        hub_id=new_traffic_hub.hub_id,
        status=status,
        data={
            "old_registry_hub": old_registry_hub.hub_id,
            "new_registry_hub": new_registry_hub.hub_id,
            "old_traffic_hub": old_traffic_hub.hub_id,
            "new_traffic_hub": new_traffic_hub.hub_id,
            "new_scope": new_scope,
            "move_action": result.action,
            "reason": result.reason,
        },
    )


def _attach_hmac_move_auth_from_step(
    contract: object,
    fields: dict[str, Any],
) -> None:
    session_id = _optional_str(fields.get("session_id"))
    move_nonce = _optional_str(fields.get("move_nonce"))
    move_counter = _optional_int(fields.get("move_counter"))
    auth_secret = _optional_str(fields.get("auth_secret"))
    move_auth_tag = _optional_str(fields.get("move_auth_tag"))

    if (
        auth_secret is not None
        and session_id is not None
        and move_nonce is not None
        and move_counter is not None
        and move_auth_tag is None
    ):
        attach_move_auth(
            contract,
            auth_secret,
            session_id=session_id,
            move_nonce=move_nonce,
            move_counter=move_counter,
        )
    else:
        contract.auth_mode = AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
        contract.session_id = session_id
        contract.move_nonce = move_nonce
        contract.move_counter = move_counter
        contract.move_auth_tag = move_auth_tag

    if bool(fields.get("tamper_move_auth_tag", False)) and contract.move_auth_tag is not None:
        contract.move_auth_tag = _tampered_tag(contract.move_auth_tag)


def _tamper_move_contract_from_step(
    contract: object,
    fields: dict[str, Any],
) -> None:
    if bool(fields.get("tamper_to_scope", False)):
        contract.to_scope = f"{contract.to_scope}.tampered"
    if bool(fields.get("tamper_new_attachment", False)):
        contract.new_attachment = f"{contract.new_attachment}_tampered"
    if bool(fields.get("tamper_old_attachment", False)):
        contract.old_attachment = f"{contract.old_attachment}_tampered"


def _step_create_invalid_move_contract(world: World, fields: dict[str, Any]) -> None:
    device_id = str(fields["device"])
    device = world.devices[device_id]
    old_registry_hub = world.registry_hubs[str(fields["old_registry_hub"])]
    new_registry_hub = world.registry_hubs[str(fields["new_registry_hub"])]
    new_scope = str(fields.get("new_scope", new_registry_hub.scope_path))

    old_record = old_registry_hub.devices.get(device_id)
    passport_id = (
        old_record.passport_id
        if old_record is not None
        else device.passport_id or f"passport_{device_id}"
    )
    contract = create_move_contract(
        device_id=device_id,
        passport_id=passport_id,
        from_scope=old_registry_hub.scope_path,
        to_scope=new_scope,
        old_attachment=old_registry_hub.hub_id,
        new_attachment=new_registry_hub.hub_id,
        valid=False,
        timestamp=world.current_time,
    )
    result = update_attachment_after_move(
        old_registry_hub,
        device_id,
        new_attachment=new_registry_hub.hub_id,
        new_scope=new_scope,
        move_contract=contract,
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} for {device_id}: {result.reason}",
        event_type=result.action,
        actor=device_id,
        target=new_registry_hub.hub_id,
        device_id=device_id,
        hub_id=old_registry_hub.hub_id,
        status=result.action,
        data={
            "old_registry_hub": old_registry_hub.hub_id,
            "new_registry_hub": new_registry_hub.hub_id,
            "new_scope": new_scope,
            "reason": result.reason,
        },
    )


def _step_simulate_duplicate_device_claim(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    result = detect_duplicate_device_claim_op(
        hub,
        str(fields["device"]),
        claiming_attachment_id=str(fields["claiming_attachment"]),
        current_time=world.current_time,
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} for {result.device_id}: {result.claiming_attachment}",
        event_type=result.action,
        actor=result.claiming_attachment,
        target=result.device_id,
        device_id=result.device_id,
        hub_id=hub.hub_id,
        status=result.action,
        data={
            "existing_attachment": result.existing_attachment,
            "claiming_attachment": result.claiming_attachment,
            "conflict_id": result.conflict_id,
            "reason": result.reason,
        },
    )


def _step_resume_lanes_after_relocation(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    result = resume_lanes_after_relocation_op(
        hub,
        str(fields["device"]),
        all_hubs=world.traffic_hubs,
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} for {result.device_id}: {result.routes}",
        event_type=result.action,
        actor=result.device_id,
        target=hub.hub_id,
        device_id=result.device_id,
        hub_id=hub.hub_id,
        status=result.action,
        data={
            "resumed_lanes": list(result.resumed_lanes),
            "failed_lanes": list(result.failed_lanes),
            "routes": dict(result.routes),
            "reason": result.reason,
        },
    )


def _step_verify_rolling_proof(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    auth_mode = str(fields.get("auth_mode", AUTH_MODE_SYMBOLIC))
    auth_secret = _optional_str(fields.get("auth_secret"))
    session_id = _optional_str(fields.get("session_id"))
    counter = _optional_int(fields.get("counter"))
    nonce = _optional_str(fields.get("nonce"))
    capability = _optional_str(fields.get("capability", fields.get("requested_capability")))
    auth_tag = _optional_str(fields.get("auth_tag"))

    if (
        auth_mode == AUTH_MODE_HMAC_SHA256_EXPERIMENTAL
        and auth_secret is not None
        and auth_tag is None
        and session_id is not None
        and counter is not None
        and nonce is not None
        and capability is not None
    ):
        auth_tag = compute_hmac_tag(
            auth_secret,
            rolling_proof_material(
                device_id=str(fields["device"]),
                hub_id=hub.hub_id,
                session_id=session_id,
                counter=counter,
                nonce=nonce,
                capability=capability,
            ),
        )
        if bool(fields.get("tamper_counter", False)):
            counter += 1
        if bool(fields.get("tamper_nonce", False)):
            nonce = f"{nonce}_tampered"

    result = verify_rolling_proof_op(
        hub,
        str(fields["device"]),
        proof_valid=bool(fields["proof_valid"]),
        current_time=world.current_time,
        auth_mode=auth_mode,
        auth_secret=auth_secret,
        auth_tag=auth_tag,
        session_id=session_id,
        counter=counter,
        nonce=nonce,
        capability=capability,
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} rolling proof for {result.device_id}",
        event_type=result.security_event.event_type if result.security_event else result.action,
        actor=result.device_id,
        target=hub.hub_id,
        device_id=result.device_id,
        hub_id=hub.hub_id,
        status=result.action,
        data={
            "success": result.success,
            "reason": result.reason,
            "security_event_type": (
                None if result.security_event is None else result.security_event.event_type
            ),
        },
    )


def _step_create_local_session(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    current_time = _optional_int(fields.get("current_time"))
    result = create_local_session_op(
        hub,
        device_id=str(fields["device"]),
        secret=str(fields["auth_secret"]),
        session_id=_optional_str(fields.get("session_id")),
        current_time=world.current_time if current_time is None else current_time,
        ttl=_optional_int(fields.get("ttl")),
        auth_mode=str(fields.get("auth_mode", AUTH_MODE_HMAC_SHA256_EXPERIMENTAL)),
    )
    world.action_results.append(result)
    session_id = None if result.session is None else result.session.session_id
    world.log(
        f"{result.status} for {fields['device']} at {hub.hub_id}",
        event_type=result.status,
        actor=str(fields["device"]),
        target=hub.hub_id,
        device_id=str(fields["device"]),
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "session_id": session_id,
            "success": result.success,
            "reason": result.reason,
        },
    )


def _step_rotate_local_session(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    current_time = _optional_int(fields.get("current_time"))
    result = rotate_local_session_op(
        hub,
        session_id=str(fields["session_id"]),
        new_secret=str(fields["new_auth_secret"]),
        current_time=world.current_time if current_time is None else current_time,
        ttl=_optional_int(fields.get("ttl")),
    )
    world.action_results.append(result)
    device_id = None if result.session is None else result.session.device_id
    world.log(
        f"{result.status} {fields['session_id']} at {hub.hub_id}",
        event_type=result.status,
        actor=device_id,
        target=hub.hub_id,
        device_id=device_id,
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "session_id": fields["session_id"],
            "success": result.success,
            "reason": result.reason,
            "rotation_index": (
                None if result.session is None else result.session.rotation_index
            ),
        },
    )


def _step_revoke_local_session(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    result = revoke_local_session_op(
        hub,
        session_id=str(fields["session_id"]),
        reason=_optional_str(fields.get("reason")),
    )
    world.action_results.append(result)
    device_id = None if result.session is None else result.session.device_id
    world.log(
        f"{result.status} {fields['session_id']} at {hub.hub_id}",
        event_type=result.status,
        actor=device_id,
        target=hub.hub_id,
        device_id=device_id,
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "session_id": fields["session_id"],
            "success": result.success,
            "reason": result.reason,
        },
    )


def _step_revoke_device_sessions(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    device_id = str(fields["device"])
    results = revoke_device_sessions_op(
        hub,
        device_id=device_id,
        reason=_optional_str(fields.get("reason")),
    )
    world.action_results.append(results[-1] if results else [])
    world.log(
        f"revoked {len(results)} session(s) for {device_id} at {hub.hub_id}",
        event_type="device_sessions_revoked",
        actor=device_id,
        target=hub.hub_id,
        device_id=device_id,
        hub_id=hub.hub_id,
        status="device_sessions_revoked",
        data={
            "session_ids": [
                result.session.session_id
                for result in results
                if result.session is not None
            ],
            "reason": fields.get("reason"),
        },
    )


def _step_revoke_device(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    device_id = str(fields["device"])
    current_time = _optional_int(fields.get("current_time"))
    result = revoke_device_op(
        hub,
        device_id=device_id,
        reason=_optional_str(fields.get("reason")),
        current_time=world.current_time if current_time is None else current_time,
    )
    world.action_results.append(result)
    world.log(
        f"{result.action} for {device_id} at {hub.hub_id}",
        event_type=(
            result.security_event.event_type
            if result.security_event is not None
            else result.action
        ),
        actor=device_id,
        target=hub.hub_id,
        device_id=device_id,
        hub_id=hub.hub_id,
        status=result.action,
        data={
            "success": result.success,
            "reason": result.reason,
        },
    )


def _step_expire_local_sessions(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    current_time = _optional_int(fields.get("current_time"))
    expired = expire_local_sessions_op(
        hub,
        current_time=world.current_time if current_time is None else current_time,
    )
    world.action_results.append(expired)
    world.log(
        f"expired {len(expired)} session(s) at {hub.hub_id}",
        event_type="sessions_expired",
        target=hub.hub_id,
        hub_id=hub.hub_id,
        status="sessions_expired",
        data={"expired_session_ids": [session.session_id for session in expired]},
    )


def _step_verify_hmac_session_proof(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    session_id = str(fields["session_id"])
    session = get_local_session(hub, session_id)
    counter = int(fields["counter"])
    nonce = str(fields["nonce"])
    capability = str(fields["requested_capability"])
    auth_tag = _optional_str(fields.get("auth_tag"))

    if auth_tag is None and session is not None:
        proof_counter = counter
        proof_nonce = nonce
        proof_secret = str(fields.get("auth_secret", session.secret))
        tamper_secret = fields.get("tamper_secret")
        if isinstance(tamper_secret, str):
            proof_secret = tamper_secret
        elif bool(tamper_secret):
            proof_secret = f"{proof_secret}_tampered"

        auth_tag = compute_hmac_tag(
            proof_secret,
            rolling_proof_material(
                device_id=session.device_id,
                hub_id=hub.hub_id,
                session_id=session.session_id,
                counter=proof_counter,
                nonce=proof_nonce,
                capability=capability,
            ),
        )
        if bool(fields.get("tamper_counter", False)):
            counter += 1
        if bool(fields.get("tamper_nonce", False)):
            nonce = f"{nonce}_tampered"

    current_time = _optional_int(fields.get("current_time"))
    result = verify_hmac_session_proof_op(
        hub,
        session_id=session_id,
        counter=counter,
        nonce=nonce,
        requested_capability=capability,
        proof=auth_tag or "",
        current_time=world.current_time if current_time is None else current_time,
    )
    world.action_results.append(result)
    world.log(
        f"{result.status} for {session_id}",
        event_type=result.status,
        actor=None if result.session is None else result.session.device_id,
        target=hub.hub_id,
        device_id=None if result.session is None else result.session.device_id,
        hub_id=hub.hub_id,
        status=result.status,
        data={
            "session_id": session_id,
            "counter": counter,
            "success": result.success,
            "reason": result.reason,
        },
    )


def _step_record_cross_tree_packet(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    count = int(fields.get("count", 1))
    for _ in range(count):
        record_cross_tree_packet_op(
            hub,
            from_branch=str(fields["from_branch"]),
            to_branch=str(fields["to_branch"]),
        )
    world.log(
        f"recorded {count} cross-tree packet(s) at {hub.hub_id}",
        event_type="cross_tree_packet_recorded",
        target=hub.hub_id,
        hub_id=hub.hub_id,
        status="recorded",
        data={
            "count": count,
            "from_branch": fields["from_branch"],
            "to_branch": fields["to_branch"],
        },
    )


def _step_recommend_traffic_bridge(world: World, fields: dict[str, Any]) -> None:
    hub = world.traffic_hubs[str(fields["traffic_hub"])]
    recommendation = recommend_traffic_bridge_op(hub)
    world.action_results.append(recommendation)
    if recommendation is None:
        world.log(
            f"no traffic bridge recommendation for {hub.hub_id}",
            event_type="no_recommendation",
            target=hub.hub_id,
            hub_id=hub.hub_id,
            status="not_recommended",
        )
        return
    world.log(
        f"recommended {recommendation.recommendation_type} for {hub.hub_id}",
        event_type=recommendation.recommendation_type,
        actor=hub.hub_id,
        target=recommendation.recommendation_type,
        hub_id=hub.hub_id,
        status=recommendation.status,
        data={
            "recommendation_id": recommendation.recommendation_id,
            "affected_hubs": list(recommendation.affected_hubs),
            "affected_branches": list(recommendation.affected_branches),
            "reason": recommendation.reason,
            "confidence": recommendation.confidence,
        },
    )


def _step_register_lane_definition(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    lane_signature = str(fields["lane_signature"])
    scope = str(fields.get("scope", hub.scope_path))

    if lane_signature == "basic_messaging:v1":
        base = make_basic_messaging_lane_definition(scope)
        lane_definition = LaneDefinition(
            lane_signature=base.lane_signature,
            scope=scope,
            description=str(fields.get("description", base.description)),
            payload_kind=_optional_str(fields.get("payload_kind", base.payload_kind)),
            schema_ref=_optional_str(fields.get("schema_ref", base.schema_ref)),
            protocol_ref=_optional_str(fields.get("protocol_ref", base.protocol_ref)),
            visibility_tier=int(fields.get("visibility_tier", base.visibility_tier.tier)),
            authority_scope=base.authority_scope,
            adapter_kinds=_optional_str_list(fields.get("adapter_kinds"))
            or list(base.adapter_kinds),
            status=str(fields.get("status", base.status.status)),
            fallback_policy=_fallback_policy(fields.get("fallback_policy"), base),
            metadata=dict(base.metadata or {}),
        )
    else:
        lane_definition = LaneDefinition(
            lane_signature=lane_signature,
            scope=scope,
            description=str(fields.get("description", "")),
            payload_kind=_optional_str(fields.get("payload_kind")),
            schema_ref=_optional_str(fields.get("schema_ref")),
            protocol_ref=_optional_str(fields.get("protocol_ref")),
            visibility_tier=int(fields.get("visibility_tier", 0)),
            adapter_kinds=_optional_str_list(fields.get("adapter_kinds")) or (),
            status=str(fields.get("status", "active")),
            fallback_policy=_fallback_policy(fields.get("fallback_policy"), None),
        )

    result = register_lane_definition_op(hub, lane_definition)
    world.action_results.append(result)
    world.log(
        f"registered lane {result.lane_signature.signature} at {hub.hub_id}",
        event_type="lane_definition_registered",
        actor=hub.hub_id,
        target=result.lane_signature.signature,
        hub_id=hub.hub_id,
        status=result.status.status,
        data=result.to_summary(),
    )


def _step_register_mailbox(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    scope = str(fields["scope"])
    local_name = str(fields["local_name"])
    address = str(
        fields.get(
            "address",
            format_mailbox_address(
                scope=scope,
                mailbox=local_name,
                resource=str(fields.get("resource", "inbox")),
            ),
        )
    )
    mailbox = MailboxIdentity(
        mailbox_id=str(fields["mailbox_id"]),
        canonical_device_id=str(fields["canonical_device_id"]),
        local_name=local_name,
        scope=scope,
        address=address,
        metadata=_optional_dict(fields.get("metadata")),
    )
    result = register_mailbox_op(hub, mailbox)
    world.action_results.append(result)
    world.log(
        f"registered mailbox {result.mailbox_id} at {hub.hub_id}",
        event_type="mailbox_registered",
        actor=result.canonical_device_id,
        target=result.mailbox_id,
        device_id=result.canonical_device_id,
        hub_id=hub.hub_id,
        status="registered",
        data=result.to_summary(),
    )


def _step_bind_mailbox_capability(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    lane_signature = str(fields["lane_signature"])
    capability = MailboxCapability(
        capability_id=str(
            fields.get("capability_id", f"cap_{lane_signature.replace(':', '_')}")
        ),
        lane_signature=lane_signature,
        direction=str(fields.get("direction", "receive")),
        enabled=bool(fields.get("enabled", True)),
        metadata=_optional_dict(fields.get("metadata")),
    )
    result = bind_mailbox_capability_op(
        hub,
        str(fields["mailbox_id"]),
        capability,
    )
    world.action_results.append(result)
    world.log(
        f"bound mailbox {result.mailbox_id} to lane {lane_signature} at {hub.hub_id}",
        event_type="mailbox_capability_bound",
        actor=result.mailbox_id,
        target=lane_signature,
        device_id=result.canonical_device_id,
        hub_id=hub.hub_id,
        status="enabled" if capability.enabled else "disabled",
        data={
            "mailbox_id": result.mailbox_id,
            "capability": capability.to_summary(),
        },
    )


def _step_register_adapter_endpoint(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    endpoint = AdapterEndpoint(
        endpoint_id=str(fields["endpoint_id"]),
        subject_id=str(fields["subject_id"]),
        subject_kind=str(fields["subject_kind"]),
        adapter_kind=str(fields["adapter_kind"]),
        status=str(fields.get("status", "unknown")),
        lane_signatures=_optional_str_list(fields.get("lane_signatures")) or (),
        scope=str(fields.get("scope", hub.scope_path)),
        host_hint=_optional_str(fields.get("host_hint")),
        port_hint=fields.get("port_hint"),
        path_hint=_optional_str(fields.get("path_hint")),
        metadata=_optional_dict(fields.get("metadata")),
    )
    result = register_adapter_endpoint_op(hub, endpoint)
    world.action_results.append(result)
    world.log(
        f"registered adapter endpoint {result.endpoint_id} at {hub.hub_id}",
        event_type="adapter_endpoint_registered",
        actor=result.subject_id,
        target=result.endpoint_id,
        hub_id=hub.hub_id,
        status=result.status.status,
        data=result.to_summary(),
    )


def _step_deliver_message(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    envelope = MessageEnvelope(
        message_id=str(fields["message_id"]),
        sender_id=str(fields["sender_id"]),
        recipient_address=str(fields["recipient_address"]),
        lane_signature=str(fields.get("lane_signature", "basic_messaging:v1")),
        payload_kind=str(fields.get("payload_kind", "text")),
        payload=fields.get("payload", ""),
        metadata=_optional_dict(fields.get("metadata")),
    )
    result = deliver_message_to_mailbox_op(hub, envelope)
    world.action_results.append(result)
    event_type = (
        "message_delivered"
        if result.status.status == "delivered"
        else "message_delivery_failed"
    )
    world.log(
        f"{event_type} {result.message_id} at {hub.hub_id}",
        event_type=event_type,
        actor=envelope.sender_id,
        target=result.resolved_mailbox_id or envelope.recipient_address,
        device_id=result.target_device_id,
        hub_id=hub.hub_id,
        status=result.status.status,
        data=result.to_summary(),
    )


def _step_evaluate_encrypted_delivery_request(
    world: World,
    fields: dict[str, Any],
) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    envelope = MessageEnvelope(
        message_id=str(fields["message_id"]),
        sender_id=str(fields["sender_id"]),
        recipient_address=str(fields["recipient_address"]),
        lane_signature=str(fields.get("lane_signature", "basic_messaging:v1")),
        payload_kind=str(fields.get("payload_kind", "text")),
        payload=fields.get("payload", ""),
        metadata=_optional_dict(fields.get("metadata")),
    )
    envelope_metadata = _policy_evaluation_envelope_metadata(fields)
    mode = _encrypted_delivery_request_mode(fields, envelope_metadata)
    policy_id = _optional_str(fields.get("policy_id"))
    mailbox_id = _optional_str(fields.get("mailbox_id"))

    if mode == "policy_check_only":
        request = EncryptedDeliveryRequest(
            request_id=str(fields["request_id"]),
            message_envelope=envelope,
            encryption_metadata=envelope_metadata,
            mode="policy_check_only",
            policy_required=True,
            policy_id=policy_id,
            mailbox_id=mailbox_id,
            lane_signature=envelope.lane_signature,
            metadata={
                "simulator_local": True,
                "request_only": True,
                "delivery_behavior_changed": False,
            },
        )
    elif mode == "symbolic_encrypted":
        if envelope_metadata is None:
            envelope_metadata = _policy_evaluation_envelope_metadata(
                {**fields, "envelope_id": f"env_{fields['message_id']}"}
            )
        request = make_symbolic_encrypted_delivery_request(
            request_id=str(fields["request_id"]),
            message_envelope=envelope,
            encryption_metadata=envelope_metadata,
            mailbox_id=mailbox_id,
            policy_id=policy_id,
        )
    else:
        request = make_plaintext_delivery_request(
            request_id=str(fields["request_id"]),
            message_envelope=envelope,
            mailbox_id=mailbox_id,
            policy_id=policy_id,
        )

    if "policy_required" in fields:
        request = _encrypted_delivery_request_with_policy_required(
            request,
            _bool_field(fields, "policy_required", request.policy_required),
        )

    result = evaluate_encrypted_delivery_request_op(
        hub,
        request,
        attempt_delivery=_bool_field(fields, "attempt_delivery", False),
        retain_policy_decision=_bool_field(fields, "retain_policy_decision", True),
        retain_result=_bool_field(fields, "retain_result", True),
    )
    result = _encrypted_delivery_result_with_registry_context(result, hub.hub_id)
    world.action_results.append(result)
    summary = summarize_encrypted_delivery_result(result)
    world.log(
        (
            "evaluated encrypted delivery request "
            f"{result.request_id} at {hub.hub_id}: {result.status.status}"
        ),
        event_type="encrypted_delivery_request_evaluated",
        actor=envelope.sender_id,
        target=result.mailbox_id or envelope.recipient_address,
        device_id=envelope.sender_id,
        hub_id=hub.hub_id,
        status=result.status.status,
        data=summary,
    )


def _step_register_encryption_identity(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    identity = EncryptionIdentity(
        encryption_identity_id=str(fields["encryption_identity_id"]),
        subject_id=str(fields["subject_id"]),
        subject_kind=str(fields["subject_kind"]),
        profile=str(fields.get("profile", DEFAULT_ENCRYPTION_PROFILE)),
        status=str(fields.get("status", "active")),
        metadata=_optional_dict(fields.get("metadata")),
    )
    result = register_encryption_identity_op(hub, identity)
    world.action_results.append(result)
    world.log(
        f"registered encryption identity {result.encryption_identity_id} at {hub.hub_id}",
        event_type="encryption_identity_registered",
        actor=result.subject_id,
        target=result.encryption_identity_id,
        hub_id=hub.hub_id,
        status=result.status,
        data=result.to_summary(),
    )


def _step_register_key_bundle_reference(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    key_bundle = KeyBundleReference(
        key_bundle_id=str(fields["key_bundle_id"]),
        encryption_identity_id=str(fields["encryption_identity_id"]),
        profile=str(fields.get("profile", DEFAULT_ENCRYPTION_PROFILE)),
        status=str(fields.get("status", "active")),
        public_ref=_optional_str(fields.get("public_ref")),
        created_order=int(fields.get("created_order", 0)),
        rotated_from=_optional_str(fields.get("rotated_from")),
        metadata=_optional_dict(fields.get("metadata")),
    )
    result = register_key_bundle_reference_op(hub, key_bundle)
    world.action_results.append(result)
    world.log(
        f"registered key bundle {result.key_bundle_id} at {hub.hub_id}",
        event_type="key_bundle_reference_registered",
        actor=result.encryption_identity_id,
        target=result.key_bundle_id,
        hub_id=hub.hub_id,
        status=result.status.status,
        data=result.to_summary(),
    )


def _step_register_mailbox_encryption_binding(
    world: World,
    fields: dict[str, Any],
) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    binding = MailboxEncryptionBinding(
        mailbox_id=str(fields["mailbox_id"]),
        encryption_identity_id=str(fields["encryption_identity_id"]),
        key_bundle_id=str(fields["key_bundle_id"]),
        required_for_lanes=_optional_str_list(fields.get("required_for_lanes")) or [],
        profile=str(fields.get("profile", DEFAULT_ENCRYPTION_PROFILE)),
        status=str(fields.get("status", "active")),
        metadata=_optional_dict(fields.get("metadata")),
    )
    result = register_mailbox_encryption_binding_op(hub, binding)
    world.action_results.append(result)
    world.log(
        f"registered mailbox encryption binding {result.mailbox_id} at {hub.hub_id}",
        event_type="mailbox_encryption_binding_registered",
        actor=result.mailbox_id,
        target=result.encryption_identity_id,
        hub_id=hub.hub_id,
        status=result.status,
        data=result.to_summary(),
    )


def _step_register_mailbox_encryption_policy(
    world: World,
    fields: dict[str, Any],
) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    policy = MailboxEncryptionPolicy(
        policy_id=str(fields["policy_id"]),
        mailbox_id=str(fields["mailbox_id"]),
        required_for_lanes=(
            _optional_str_list(fields.get("required_for_lanes"))
            or ["basic_messaging:v1"]
        ),
        allowed_profiles=(
            _optional_str_list(fields.get("allowed_profiles"))
            or [DEFAULT_ENCRYPTION_PROFILE]
        ),
        require_active_identity=_bool_field(fields, "require_active_identity", True),
        require_usable_key_bundle=_bool_field(
            fields,
            "require_usable_key_bundle",
            True,
        ),
        allow_plaintext_fallback=_bool_field(
            fields,
            "allow_plaintext_fallback",
            False,
        ),
        metadata=_optional_dict(fields.get("metadata")),
    )
    result = register_mailbox_encryption_policy_op(hub, policy)
    world.action_results.append(result)
    world.log(
        f"registered mailbox encryption policy {result.policy_id} at {hub.hub_id}",
        event_type="mailbox_encryption_policy_registered",
        actor=result.mailbox_id,
        target=result.policy_id,
        hub_id=hub.hub_id,
        status="registered",
        data=result.to_summary(),
    )


def _step_evaluate_mailbox_encryption_policy(
    world: World,
    fields: dict[str, Any],
) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    envelope_metadata = _policy_evaluation_envelope_metadata(fields)
    result = evaluate_registered_policy_op(
        hub,
        mailbox_id=str(fields["mailbox_id"]),
        lane_signature=str(fields["lane_signature"]),
        message_id=_optional_str(fields.get("message_id")),
        envelope_metadata=envelope_metadata,
    )
    result = _policy_decision_with_registry_context(result, hub.hub_id)
    world.action_results.append(result)
    world.log(
        (
            "evaluated mailbox encryption policy for "
            f"{result.mailbox_id} at {hub.hub_id}: {result.status.status}"
        ),
        event_type="mailbox_encryption_policy_evaluated",
        actor=result.mailbox_id,
        target=result.policy_id,
        hub_id=hub.hub_id,
        status=result.status.status,
        data=result.to_summary(),
    )


def _step_hold_stream_offer(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    base_offer = make_stream_offer(
        offer_id=str(fields["offer_id"]),
        requester_id=str(fields["requester_id"]),
        target_handle=str(fields["target_handle"]),
        lane_signature=str(fields["lane_signature"]),
        requested_mode=str(fields.get("requested_mode", "message")),
        visibility_tier=int(fields.get("visibility_tier", 0)),
        rendezvous_scope=_optional_str(fields.get("rendezvous_scope")),
        created_order=int(fields.get("created_order", 0)),
        expires_order=_optional_int(fields.get("expires_order")),
        metadata=_optional_dict(fields.get("metadata")),
    )
    status = fields.get("status")
    offer = base_offer
    if status is not None:
        offer = StreamOffer(
            offer_id=base_offer.offer_id,
            requester_id=base_offer.requester_id,
            target_handle=base_offer.target_handle,
            lane_signature=base_offer.lane_signature,
            requested_mode=base_offer.requested_mode,
            visibility_tier=base_offer.visibility_tier,
            status=str(status),
            rendezvous_scope=base_offer.rendezvous_scope,
            created_order=base_offer.created_order,
            expires_order=base_offer.expires_order,
            metadata=base_offer.metadata,
        )
    result = hold_stream_offer_op(
        hub,
        offer,
        replace_existing=_bool_field(fields, "replace_existing", False),
    )
    world.action_results.append(result)
    world.log(
        f"held stream offer {result.offer_id} at {hub.hub_id}: {result.status.status}",
        event_type="stream_offer_held",
        actor=result.requester_id,
        target=result.target_handle,
        hub_id=hub.hub_id,
        status=result.status.status,
        data=result.to_summary(),
    )


def _step_poll_held_stream_offers(world: World, fields: dict[str, Any]) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    request = make_rendezvous_request(
        request_id=str(fields["request_id"]),
        offer_id=str(fields["offer_id"]),
        polling_hub_id=str(fields["polling_hub_id"]),
        requester_id=str(fields["requester_id"]),
        target_scope=str(fields["target_scope"]),
        visibility_tier=int(fields.get("visibility_tier", 0)),
        metadata=_optional_dict(fields.get("metadata")),
    )
    result = poll_held_stream_offers_op(
        hub,
        request,
        lane_signature=_optional_str(fields.get("lane_signature")),
        requested_mode=_optional_str(fields.get("requested_mode")),
        active_only=_bool_field(fields, "active_only", True),
        current_order=_optional_int(fields.get("current_order")),
    )
    record_rendezvous_poll_result_op(hub, result)
    world.action_results.append(request)
    world.action_results.append(result)
    world.log(
        (
            "polled held stream offers "
            f"{request.request_id} at {hub.hub_id}: {result.status.status}"
        ),
        event_type="stream_offers_polled",
        actor=request.polling_hub_id,
        target=hub.hub_id,
        hub_id=hub.hub_id,
        status=result.status.status,
        data=result.to_summary(),
    )


def _step_mark_stream_offers_discoverable(
    world: World,
    fields: dict[str, Any],
) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    updated = mark_stream_offers_discoverable_op(
        hub,
        _optional_str_list(fields.get("offer_ids")) or [],
        metadata=_optional_dict(fields.get("metadata")),
    )
    world.action_results.extend(updated)
    world.log(
        f"marked stream offers discoverable at {hub.hub_id}: {len(updated)}",
        event_type="stream_offers_marked_discoverable",
        target=hub.hub_id,
        hub_id=hub.hub_id,
        status="discoverable",
        data={"offers": [offer.to_summary() for offer in updated]},
    )


def _step_evaluate_lane_admission_policy(
    world: World,
    fields: dict[str, Any],
) -> None:
    hub = world.registry_hubs[str(fields["registry_hub"])]
    offer = get_held_stream_offer_op(hub, str(fields["offer_id"]))
    if offer is None:
        raise KeyError(f"held stream offer is not registered: {fields['offer_id']}")

    policy = make_lane_admission_policy(
        policy_id=str(fields["policy_id"]),
        hub_id=str(fields["hub_id"]),
        allowed_lane_signatures=_optional_str_list(
            fields.get("allowed_lane_signatures")
        ),
        denied_lane_signatures=_optional_str_list(fields.get("denied_lane_signatures")),
        allowed_requester_ids=_optional_str_list(fields.get("allowed_requester_ids")),
        denied_requester_ids=_optional_str_list(fields.get("denied_requester_ids")),
        allowed_target_scopes=_optional_str_list(fields.get("allowed_target_scopes")),
        denied_target_scopes=_optional_str_list(fields.get("denied_target_scopes")),
        max_visibility_tier=_optional_int(fields.get("max_visibility_tier")),
        require_discoverable=_bool_field(fields, "require_discoverable", False),
        default_status=str(fields.get("default_status", "hold")),
        metadata=_optional_dict(fields.get("metadata")),
    )
    request = _find_rendezvous_request(world, fields)
    poll_result = _find_rendezvous_poll_result(world, fields)
    if request is None and fields.get("request_id") is not None:
        target_scope = _optional_str(fields.get("target_scope"))
        if target_scope is None and poll_result is not None:
            target_scope = poll_result.target_scope
        if target_scope is not None:
            request = RendezvousRequest(
                request_id=str(fields["request_id"]),
                offer_id=offer.offer_id,
                polling_hub_id=str(fields.get("polling_hub_id", policy.hub_id)),
                requester_id=offer.requester_id,
                target_scope=target_scope,
                visibility_tier=offer.visibility_tier,
                metadata={"simulator_local": True, "request_only": True},
            )
    result = evaluate_lane_admission_policy_op(
        policy,
        offer,
        request=request,
        poll_result=poll_result,
        decision_id=_optional_str(fields.get("decision_id")),
        metadata=_optional_dict(fields.get("decision_metadata")),
    )
    record_lane_admission_decision_op(hub, result)
    world.action_results.append(result)
    world.log(
        (
            "evaluated lane admission "
            f"{result.decision_id} at {hub.hub_id}: {result.status.status}"
        ),
        event_type="lane_admission_policy_evaluated",
        actor=result.requester_id,
        target=result.offer_id,
        hub_id=hub.hub_id,
        status=result.status.status,
        data=result.to_summary(),
    )


def _step_advance_time(world: World, fields: dict[str, Any]) -> None:
    ticks = int(fields.get("ticks", 1))
    world.advance_time(ticks)
    world.log(
        f"advanced time by {ticks}",
        event_type="time_advanced",
        status="advanced",
        data={"ticks": ticks},
    )


def _configs(value: Any, key_name: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [dict(item) for item in value]
    if isinstance(value, dict):
        configs = []
        for key, item in value.items():
            config = dict(item) if isinstance(item, dict) else {}
            config.setdefault(key_name, key)
            configs.append(config)
        return configs
    raise TypeError("Scenario setup sections must be lists or mappings")


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_str_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _optional_policy(value: Any) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError("alias_authority_policy must be a mapping")
    return dict(value)


def _optional_dict(value: Any) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError("metadata must be a mapping")
    return dict(value)


def _find_rendezvous_request(
    world: World,
    fields: dict[str, Any],
) -> RendezvousRequest | None:
    request_id = fields.get("poll_request_id", fields.get("request_id"))
    if request_id is None:
        return None
    request_id = str(request_id)
    for result in reversed(world.action_results):
        if isinstance(result, RendezvousRequest) and result.request_id == request_id:
            return result
    return None


def _find_rendezvous_poll_result(
    world: World,
    fields: dict[str, Any],
) -> RendezvousPollResult | None:
    request_id = fields.get("poll_result_request_id")
    if request_id is None:
        request_id = fields.get("poll_request_id")
    if request_id is None:
        return None
    request_id = str(request_id)
    for result in reversed(world.action_results):
        if isinstance(result, RendezvousPollResult) and result.request_id == request_id:
            return result
    return None


def _bool_field(fields: dict[str, Any], field_name: str, default: bool) -> bool:
    value = fields.get(field_name, default)
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean")
    return value


def _encrypted_delivery_request_mode(
    fields: dict[str, Any],
    envelope_metadata: EncryptedEnvelopeMetadata | None,
) -> str:
    mode = fields.get("mode")
    if mode is not None:
        return str(mode)
    if envelope_metadata is not None:
        return "symbolic_encrypted"
    return "plaintext"


def _encrypted_delivery_request_with_policy_required(request: Any, value: bool) -> Any:
    return request.__class__(
        request_id=request.request_id,
        message_envelope=request.message_envelope,
        encryption_metadata=request.encryption_metadata,
        mode=request.mode,
        policy_required=value,
        policy_id=request.policy_id,
        mailbox_id=request.mailbox_id,
        lane_signature=request.lane_signature,
        metadata=request.metadata,
    )


def _encrypted_delivery_result_with_registry_context(result: Any, hub_id: str) -> Any:
    metadata = dict(result.metadata or {})
    metadata["registry_hub"] = hub_id
    return result.__class__(
        request_id=result.request_id,
        message_id=result.message_id,
        mailbox_id=result.mailbox_id,
        lane_signature=result.lane_signature,
        gate_decision=result.gate_decision,
        delivery_result=result.delivery_result,
        status=result.status,
        reason=result.reason,
        delivery_attempted=result.delivery_attempted,
        delivery_allowed=result.delivery_allowed,
        policy_required=result.policy_required,
        metadata=metadata,
    )


def _policy_evaluation_envelope_metadata(
    fields: dict[str, Any],
) -> EncryptedEnvelopeMetadata | None:
    envelope_field_names = {
        "envelope_id",
        "encryption_identity_id",
        "key_bundle_id",
        "profile",
        "state",
        "status",
        "algorithm_ref",
        "ciphertext_ref",
        "plaintext_ref",
    }
    if not any(field_name in fields for field_name in envelope_field_names):
        return None

    message_id = str(fields.get("message_id", "msg_symbolic_encryption_policy"))
    envelope_id = str(fields.get("envelope_id", f"env_{message_id}"))
    return EncryptedEnvelopeMetadata(
        envelope_id=envelope_id,
        message_id=message_id,
        encryption_identity_id=_optional_str(fields.get("encryption_identity_id")),
        key_bundle_id=_optional_str(fields.get("key_bundle_id")),
        profile=str(fields.get("profile", DEFAULT_ENCRYPTION_PROFILE)),
        state=str(fields.get("state", "symbolically_encrypted")),
        status=str(fields.get("status", "ready")),
        algorithm_ref=_optional_str(
            fields.get("algorithm_ref", DEFAULT_SYMBOLIC_ENVELOPE_ALGORITHM_REF)
        ),
        ciphertext_ref=_optional_str(fields.get("ciphertext_ref")),
        plaintext_ref=_optional_str(fields.get("plaintext_ref")),
        metadata=_optional_dict(fields.get("envelope_metadata")),
    )


def _policy_decision_with_registry_context(
    decision: EncryptionPolicyDecision,
    registry_hub_id: str,
) -> EncryptionPolicyDecision:
    metadata = dict(decision.metadata or {})
    metadata["registry_hub"] = registry_hub_id
    return EncryptionPolicyDecision(
        policy_id=decision.policy_id,
        mailbox_id=decision.mailbox_id,
        lane_signature=decision.lane_signature,
        message_id=decision.message_id,
        status=decision.status,
        reason=decision.reason,
        encryption_required=decision.encryption_required,
        envelope_accepted=decision.envelope_accepted,
        profile=decision.profile,
        encryption_identity_id=decision.encryption_identity_id,
        key_bundle_id=decision.key_bundle_id,
        metadata=metadata,
    )


def _fallback_policy(
    value: Any,
    base: LaneDefinition | None,
) -> LaneDeliveryFallbackPolicy:
    if value is None:
        return (
            base.fallback_policy
            if base is not None
            else LaneDeliveryFallbackPolicy()
        )
    if not isinstance(value, dict):
        raise TypeError("fallback_policy must be a mapping")
    return LaneDeliveryFallbackPolicy(**dict(value))


def _link_metrics(link_config: dict[str, Any]) -> LinkMetrics:
    return LinkMetrics(
        latency_ms=int(link_config.get("latency_ms", 1)),
        congestion=str(link_config.get("congestion", "low")),
        trust=str(link_config.get("trust", "verified")),
        stability=str(link_config.get("stability", "stable")),
    )


def _tampered_tag(tag: str) -> str:
    return ("0" if tag[:1] != "0" else "1") + tag[1:]
