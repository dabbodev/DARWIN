import json
from copy import deepcopy

from darwin.models.device import Device
from darwin.models.hub import RegistryHub
from darwin.registry.alias_authority import claim_alias_through_authority_chain
from darwin.registry.operations import register_device
from darwin.sim.export import export_result, export_snapshot
from darwin.sim.runner import run_scenario
from darwin.sim.world import World


def test_detailed_snapshot_includes_success_and_fallback_authority_outcomes():
    result = run_scenario("scenarios/042_authority_outcome_history_success.yaml")

    compact_snapshot = result.world.snapshot()
    snapshot = result.final_snapshot
    home_history = snapshot["registry_hubs"]["registry_home_001"][
        "authority_outcome_history"
    ]
    lab_history = snapshot["registry_hubs"]["registry_lab_001"][
        "authority_outcome_history"
    ]

    assert compact_snapshot["registry_hubs"] == [
        "registry_family_001",
        "registry_global_001",
        "registry_home_001",
        "registry_lab_001",
        "registry_lab_family_001",
    ]
    assert "authority_outcome_history" not in compact_snapshot
    assert home_history == [
        {
            "record_id": "authority_outcome:registry_home_001:0001",
            "requested_alias": "global.server",
            "granted_alias": "global.server",
            "target_device": "dev_A9F3",
            "requesting_hub": "registry_home_001",
            "authority_ceiling": "global",
            "final_status": "approved_here",
            "status": "claimed",
            "reason": None,
            "decision_count": 3,
            "path_hubs": [
                "registry_home_001",
                "registry_family_001",
                "registry_global_001",
            ],
            "decisions": home_history[0]["decisions"],
            "fallback_used": False,
            "conflict_detected": False,
            "policy_denied": False,
            "path_broken": False,
        }
    ]
    assert lab_history[0]["record_id"] == "authority_outcome:registry_lab_001:0001"
    assert lab_history[0]["requested_alias"] == "global.edge"
    assert lab_history[0]["granted_alias"] == "global.family.david.edge"
    assert lab_history[0]["fallback_used"] is True
    assert lab_history[0]["policy_denied"] is False
    assert lab_history[0]["path_broken"] is False
    json.dumps(snapshot, sort_keys=True)


def test_snapshot_and_result_exports_include_denial_authority_outcomes(tmp_path):
    result = run_scenario("scenarios/043_authority_outcome_history_denials.yaml")
    snapshot_path = tmp_path / "snapshot.json"
    result_path = tmp_path / "result.json"

    export_snapshot(result, snapshot_path)
    export_result(result, result_path)

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    exported_result = json.loads(result_path.read_text(encoding="utf-8"))
    conflict_history = snapshot["registry_hubs"]["registry_conflict_home_001"][
        "authority_outcome_history"
    ]
    policy_history = snapshot["registry_hubs"]["registry_policy_home_001"][
        "authority_outcome_history"
    ]
    broken_history = exported_result["final_snapshot"]["registry_hubs"][
        "registry_broken_home_001"
    ]["authority_outcome_history"]

    assert conflict_history[0]["final_status"] == "name_taken"
    assert conflict_history[0]["status"] == "conflict"
    assert conflict_history[0]["conflict_detected"] is True
    assert policy_history[0]["final_status"] == "policy_denied"
    assert policy_history[0]["status"] == "rejected"
    assert policy_history[0]["policy_denied"] is True
    assert broken_history[0]["final_status"] == "authority_path_broken"
    assert broken_history[0]["status"] == "authority_path_broken"
    assert broken_history[0]["path_broken"] is True


def test_authority_outcome_snapshot_ordering_is_deterministic_and_read_only():
    world = World()
    hub = RegistryHub(hub_id="registry_us_001", scope_path="global.us")
    device = Device(device_id="dev_A9F3", label="server")
    world.add_registry_hub(hub)
    world.add_device(device)
    register_device(hub, device)

    claim_alias_through_authority_chain(
        world.registry_hubs,
        hub.hub_id,
        "global.zeta",
        "zeta",
        device.device_id,
    )
    claim_alias_through_authority_chain(
        world.registry_hubs,
        hub.hub_id,
        "global.alpha",
        "alpha",
        device.device_id,
    )
    before_history = deepcopy(hub.authority_outcome_history)

    snapshot = world.snapshot(detailed=True)
    history = snapshot["registry_hubs"]["registry_us_001"][
        "authority_outcome_history"
    ]
    history[0]["decisions"][0]["reason"] = "mutated_snapshot_copy"

    assert [record["record_id"] for record in history] == [
        "authority_outcome:registry_us_001:0001",
        "authority_outcome:registry_us_001:0002",
    ]
    assert [record["requested_alias"] for record in history] == [
        "global.zeta",
        "global.alpha",
    ]
    assert hub.authority_outcome_history == before_history
