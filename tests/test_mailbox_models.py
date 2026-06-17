import json
from copy import deepcopy

import pytest

from darwin.models import (
    DarwinMailboxAddress,
    MailboxCapability,
    MailboxIdentity,
    format_mailbox_address,
    is_mailbox_address,
    parse_lane_signature,
    parse_mailbox_address,
)


def test_parse_valid_mailbox_address():
    address = parse_mailbox_address("darwin://global.chat.neo/inbox")

    assert address == DarwinMailboxAddress(
        raw="darwin://global.chat.neo/inbox",
        scheme="darwin",
        scope="global.chat",
        mailbox="neo",
        resource="inbox",
    )


def test_format_mailbox_address():
    assert (
        format_mailbox_address(scope="global.chat", mailbox="neo", resource="inbox")
        == "darwin://global.chat.neo/inbox"
    )


def test_format_mailbox_address_defaults_to_inbox_resource():
    assert format_mailbox_address(scope="global.chat", mailbox="neo") == (
        "darwin://global.chat.neo/inbox"
    )


def test_mailbox_address_round_trip_format_and_parse():
    raw = format_mailbox_address(scope="global.chat", mailbox="neo", resource="inbox")
    parsed = parse_mailbox_address(raw)

    assert parsed.raw == raw
    assert parsed.to_summary() == {
        "raw": "darwin://global.chat.neo/inbox",
        "scheme": "darwin",
        "scope": "global.chat",
        "mailbox": "neo",
        "resource": "inbox",
    }


def test_invalid_scheme_rejected():
    with pytest.raises(ValueError, match="darwin://"):
        parse_mailbox_address("https://global.chat.neo/inbox")


def test_empty_scope_rejected():
    with pytest.raises(ValueError, match="scope"):
        parse_mailbox_address("darwin://.neo/inbox")


def test_empty_mailbox_rejected():
    with pytest.raises(ValueError, match="mailbox"):
        parse_mailbox_address("darwin://global.chat./inbox")


def test_empty_resource_rejected():
    with pytest.raises(ValueError, match="resource"):
        parse_mailbox_address("darwin://global.chat.neo/")


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "darwin://global.chat.neo",
        "darwin://neo/inbox",
        "darwin://global..chat.neo/inbox",
        "darwin://global.chat.neo/inbox/archive",
        "darwin://global.chat.ne o/inbox",
        "darwin://global.chat.neo/in box",
        "darwin://global.chat.neo/inbox?debug=true",
    ],
)
def test_malformed_mailbox_addresses_rejected(raw):
    with pytest.raises(ValueError):
        parse_mailbox_address(raw)


def test_parse_mailbox_address_rejects_non_string():
    with pytest.raises(TypeError):
        parse_mailbox_address(42)  # type: ignore[arg-type]


def test_is_mailbox_address_true_false_behavior():
    assert is_mailbox_address("darwin://global.chat.neo/inbox") is True
    assert is_mailbox_address("darwin://global.chat.neo") is False
    assert is_mailbox_address("https://global.chat.neo/inbox") is False
    assert is_mailbox_address(42) is False  # type: ignore[arg-type]


def test_address_summary_is_json_safe():
    summary = parse_mailbox_address("darwin://global.chat.neo/inbox").to_summary()

    assert summary == {
        "raw": "darwin://global.chat.neo/inbox",
        "scheme": "darwin",
        "scope": "global.chat",
        "mailbox": "neo",
        "resource": "inbox",
    }
    json.dumps(summary)


def test_mailbox_capability_summary_is_json_safe():
    capability = MailboxCapability(
        capability_id="cap_basic_messaging",
        lane_signature=parse_lane_signature("basic_messaging:v1"),
        direction="receive",
        enabled=True,
        metadata={"simulator_local": True, "labels": ["mailbox", "demo"]},
    )

    summary = capability.to_summary()

    assert summary == {
        "capability_id": "cap_basic_messaging",
        "lane_signature": "basic_messaging:v1",
        "direction": "receive",
        "enabled": True,
        "metadata": {"simulator_local": True, "labels": ["mailbox", "demo"]},
    }
    json.dumps(summary)


def test_mailbox_capability_can_reference_basic_messaging_lane_signature():
    capability = MailboxCapability(
        capability_id="cap_basic_messaging",
        lane_signature="basic_messaging:v1",
    )

    assert capability.lane_signature == "basic_messaging:v1"


def test_mailbox_identity_summary_is_json_safe():
    identity = MailboxIdentity(
        mailbox_id="mailbox_neo",
        canonical_device_id="dev_A9F3",
        local_name="neo",
        scope="global.chat",
        address="darwin://global.chat.neo/inbox",
        capabilities=(
            MailboxCapability(
                capability_id="cap_basic_messaging",
                lane_signature="basic_messaging:v1",
                metadata={"simulator_local": True},
            ),
        ),
        metadata={"owner_label": "Neo"},
    )

    summary = identity.to_summary()

    assert summary == {
        "mailbox_id": "mailbox_neo",
        "canonical_device_id": "dev_A9F3",
        "local_name": "neo",
        "scope": "global.chat",
        "address": {
            "raw": "darwin://global.chat.neo/inbox",
            "scheme": "darwin",
            "scope": "global.chat",
            "mailbox": "neo",
            "resource": "inbox",
        },
        "capabilities": [
            {
                "capability_id": "cap_basic_messaging",
                "lane_signature": "basic_messaging:v1",
                "direction": "receive",
                "enabled": True,
                "metadata": {"simulator_local": True},
            }
        ],
        "metadata": {"owner_label": "Neo"},
    }
    json.dumps(summary)


def test_mailbox_identity_can_reference_canonical_device_without_rewriting_identity():
    identity = MailboxIdentity(
        mailbox_id="mailbox_neo",
        canonical_device_id="dev_A9F3",
        local_name="neo",
        scope="global.chat",
        address=format_mailbox_address("global.chat", "neo"),
    )

    assert identity.canonical_device_id == "dev_A9F3"
    assert identity.mailbox_id == "mailbox_neo"
    assert identity.address.raw == "darwin://global.chat.neo/inbox"


def test_mailbox_identity_rejects_address_scope_or_local_name_mismatch():
    with pytest.raises(ValueError, match="scope"):
        MailboxIdentity(
            mailbox_id="mailbox_neo",
            canonical_device_id="dev_A9F3",
            local_name="neo",
            scope="global.chat",
            address="darwin://global.remote.neo/inbox",
        )

    with pytest.raises(ValueError, match="local_name"):
        MailboxIdentity(
            mailbox_id="mailbox_neo",
            canonical_device_id="dev_A9F3",
            local_name="neo",
            scope="global.chat",
            address="darwin://global.chat.trinity/inbox",
        )


def test_mailbox_models_reject_non_json_safe_metadata():
    with pytest.raises(TypeError):
        MailboxCapability(
            capability_id="cap_bad",
            lane_signature="basic_messaging:v1",
            metadata={"bad": object()},
        )

    with pytest.raises(TypeError):
        MailboxIdentity(
            mailbox_id="mailbox_neo",
            canonical_device_id="dev_A9F3",
            local_name="neo",
            scope="global.chat",
            address="darwin://global.chat.neo/inbox",
            metadata={"bad": object()},
        )


def test_helpers_are_pure_and_deterministic():
    raw = "darwin://global.chat.neo/inbox"
    capability = MailboxCapability(
        capability_id="cap_basic_messaging",
        lane_signature="basic_messaging:v1",
        metadata={"labels": ["mailbox"]},
    )
    identity = MailboxIdentity(
        mailbox_id="mailbox_neo",
        canonical_device_id="dev_A9F3",
        local_name="neo",
        scope="global.chat",
        address=raw,
        capabilities=(capability,),
    )
    before_capability = deepcopy(capability.to_summary())
    before_identity = deepcopy(identity.to_summary())

    first_parse = parse_mailbox_address(raw)
    second_parse = parse_mailbox_address(raw)
    first_format = format_mailbox_address("global.chat", "neo")
    second_format = format_mailbox_address("global.chat", "neo")

    assert first_parse == second_parse
    assert first_format == second_format == raw
    assert capability.to_summary() == before_capability
    assert identity.to_summary() == before_identity
