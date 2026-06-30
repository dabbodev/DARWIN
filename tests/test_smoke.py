from darwin import __version__
from darwin.cli.main import main
from darwin.models.device import Device
from darwin.models.hub import RegistryHub, TrafficHub
from darwin.sim.world import World


def test_package_imports():
    assert __version__ == "1.4.0"


def test_cli_version_reports_package_version(capsys):
    exit_code = main(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "darwin-sim 1.4.0"


def test_world_can_hold_device_and_hubs():
    world = World()
    device = Device(device_id="dev_A9F3", label="my_pc")
    registry_hub = RegistryHub(hub_id="hub_home_001", scope_path="global.family.david.home")
    traffic_hub = TrafficHub(hub_id="hub_home_001")

    world.add_device(device)
    world.add_registry_hub(registry_hub)
    world.add_traffic_hub(traffic_hub)
    device.attach("hub_home_001")
    traffic_hub.attach_device(device.device_id)

    assert world.snapshot() == {
        "time": 0,
        "devices": ["dev_A9F3"],
        "registry_hubs": ["hub_home_001"],
        "traffic_hubs": ["hub_home_001"],
        "lanes": [],
    }
    assert device.state == "online"
    assert "dev_A9F3" in traffic_hub.direct_attachments
