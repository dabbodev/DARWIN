import json
from copy import deepcopy

import pytest

from darwin.models import (
    LaneIntentAdvertisement,
    LaneSignature,
    LaneTrustContext,
    can_discover_lane_intent,
    filter_discoverable_lane_intents,
    format_lane_signature,
    is_lane_signature,
    parse_lane_signature,
)


def _advertisement(
    visibility_tier: int,
    *,
    advertisement_id: str | None = None,
    scope: str = "global.chat.local",
    authorized_observers: tuple[str, ...] = (),
) -> LaneIntentAdvertisement:
    return LaneIntentAdvertisement(
        advertisement_id=advertisement_id or f"lane_intent_{visibility_tier}",
        subject_id=f"mailbox_{visibility_tier}",
        subject_kind="mailbox",
        lane_signature=parse_lane_signature("basic_messaging:v1"),
        visibility_tier=visibility_tier,
        scope=scope,
        authorized_observers=authorized_observers,
        metadata={"simulator_local": True, "labels": ["demo", "mailbox"]},
    )


def test_format_lane_signature():
    assert format_lane_signature("basic_messaging", "v1") == "basic_messaging:v1"


def test_parse_valid_basic_messaging_signature():
    signature = parse_lane_signature("basic_messaging:v1")

    assert signature == LaneSignature(lane_id="basic_messaging", version="v1")
    assert signature.signature == "basic_messaging:v1"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "basic_messaging",
        "basic_messaging:",
        ":v1",
        "basic:messaging:v1",
        "basic messaging:v1",
        " basic_messaging:v1",
    ],
)
def test_parse_lane_signature_rejects_malformed_signatures(raw):
    with pytest.raises(ValueError):
        parse_lane_signature(raw)


def test_parse_lane_signature_rejects_non_string():
    with pytest.raises(TypeError):
        parse_lane_signature(42)  # type: ignore[arg-type]


def test_is_lane_signature_true_false_behavior():
    assert is_lane_signature("basic_messaging:v1") is True
    assert is_lane_signature("basic_messaging") is False
    assert is_lane_signature("basic:messaging:v1") is False
    assert is_lane_signature(42) is False  # type: ignore[arg-type]


def test_lane_signature_summary_is_json_safe():
    summary = parse_lane_signature("basic_messaging:v1").to_summary()

    assert summary == {
        "lane_id": "basic_messaging",
        "version": "v1",
        "signature": "basic_messaging:v1",
        "direction": "receive",
        "payload_kind": "symbolic_message_envelope",
        "recipient_kind": "mailbox",
        "required_capability": "basic_messaging",
        "auth_policy": "authorization_required",
        "adapter_kind": "mailbox_adapter",
    }
    json.dumps(summary)


def test_lane_intent_advertisement_summary_is_json_safe():
    advertisement = _advertisement(5, authorized_observers=("dev_A9F3",))

    summary = advertisement.to_summary()

    assert summary == {
        "advertisement_id": "lane_intent_5",
        "subject_id": "mailbox_5",
        "subject_kind": "mailbox",
        "lane_signature": parse_lane_signature("basic_messaging:v1").to_summary(),
        "visibility_tier": 5,
        "scope": "global.chat.local",
        "authorized_observers": ["dev_A9F3"],
        "metadata": {"simulator_local": True, "labels": ["demo", "mailbox"]},
    }
    json.dumps(summary)


def test_lane_intent_rejects_non_json_safe_metadata():
    with pytest.raises(TypeError):
        LaneIntentAdvertisement(
            advertisement_id="lane_intent_bad_metadata",
            subject_id="mailbox_bad",
            subject_kind="mailbox",
            lane_signature=parse_lane_signature("basic_messaging:v1"),
            visibility_tier=0,
            scope="global.chat.local",
            metadata={"bad": object()},
        )


def test_visibility_tier_0_is_discoverable_by_anyone():
    advertisement = _advertisement(0)
    anonymous = LaneTrustContext(requester_id="anonymous")

    assert can_discover_lane_intent(advertisement, anonymous) is True


def test_visibility_tier_1_is_discoverable_only_within_matching_local_scope():
    advertisement = _advertisement(1, scope="global.chat.local")
    same_scope = LaneTrustContext(
        requester_id="dev_A9F3",
        requester_scope="global.chat.local",
    )
    other_scope = LaneTrustContext(
        requester_id="dev_B2C8",
        requester_scope="global.chat.remote",
    )

    assert can_discover_lane_intent(advertisement, same_scope) is True
    assert can_discover_lane_intent(advertisement, other_scope) is False


def test_visibility_tier_2_requires_authenticated_trust_context():
    advertisement = _advertisement(2)
    unauthenticated = LaneTrustContext(requester_id="dev_A9F3", authenticated=False)
    authenticated = LaneTrustContext(requester_id="dev_A9F3", authenticated=True)

    assert can_discover_lane_intent(advertisement, unauthenticated) is False
    assert can_discover_lane_intent(advertisement, authenticated) is True


def test_visibility_tier_3_requires_scoped_trust():
    advertisement = _advertisement(3, scope="global.chat.local")
    untrusted = LaneTrustContext(
        requester_id="dev_A9F3",
        requester_scope="global.chat.local",
    )
    trusted = LaneTrustContext(
        requester_id="dev_A9F3",
        trusted_scopes=("global.chat.local",),
    )

    assert can_discover_lane_intent(advertisement, untrusted) is False
    assert can_discover_lane_intent(advertisement, trusted) is True


def test_visibility_tier_4_requires_delegated_trust_path():
    advertisement = _advertisement(4, scope="global.chat.local")
    undelegated = LaneTrustContext(requester_id="dev_A9F3")
    delegated = LaneTrustContext(
        requester_id="dev_A9F3",
        requester_scope="global.chat.remote",
        delegated_trust_paths=("global.chat.remote->global.chat.local",),
    )

    assert can_discover_lane_intent(advertisement, undelegated) is False
    assert can_discover_lane_intent(advertisement, delegated) is True


def test_visibility_tier_5_requires_explicit_observer_permission():
    advertisement = _advertisement(5, authorized_observers=("dev_A9F3",))
    denied = LaneTrustContext(requester_id="dev_B2C8")
    allowed_by_observer = LaneTrustContext(requester_id="dev_A9F3")
    allowed_by_permission = LaneTrustContext(
        requester_id="dev_C7D1",
        explicit_permissions=("lane_intent_5",),
    )

    assert can_discover_lane_intent(advertisement, denied) is False
    assert can_discover_lane_intent(advertisement, allowed_by_observer) is True
    assert can_discover_lane_intent(advertisement, allowed_by_permission) is True


def test_visibility_does_not_imply_use_authorization():
    advertisement = _advertisement(0)
    requester = LaneTrustContext(requester_id="anonymous")

    assert can_discover_lane_intent(advertisement, requester) is True
    assert advertisement.lane_signature.auth_policy == "authorization_required"
    assert advertisement.lane_signature.required_capability == "basic_messaging"


def test_filter_discoverable_lane_intents_preserves_deterministic_ordering():
    advertisements = [
        _advertisement(5, advertisement_id="private", authorized_observers=("dev_A9F3",)),
        _advertisement(0, advertisement_id="public"),
        _advertisement(1, advertisement_id="local", scope="global.chat.local"),
        _advertisement(2, advertisement_id="authenticated"),
    ]
    requester = LaneTrustContext(
        requester_id="dev_A9F3",
        requester_scope="global.chat.local",
        authenticated=False,
    )

    filtered = filter_discoverable_lane_intents(advertisements, requester)

    assert [advertisement.advertisement_id for advertisement in filtered] == [
        "private",
        "public",
        "local",
    ]


def test_helpers_are_pure_and_deterministic():
    advertisement = _advertisement(4, scope="global.chat.local")
    requester = LaneTrustContext(
        requester_id="dev_A9F3",
        requester_scope="global.chat.remote",
        delegated_trust_paths=("global.chat.remote->global.chat.local",),
    )
    before_advertisement = deepcopy(advertisement.to_summary())
    before_requester = deepcopy(requester)

    first = can_discover_lane_intent(advertisement, requester)
    second = can_discover_lane_intent(advertisement, requester)

    assert first is True
    assert second is True
    assert advertisement.to_summary() == before_advertisement
    assert requester == before_requester
