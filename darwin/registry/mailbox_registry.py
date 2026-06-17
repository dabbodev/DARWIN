"""Simulator-local mailbox registration and lane binding helpers."""

from __future__ import annotations

from dataclasses import replace

from darwin.models.hub import RegistryHub
from darwin.models.lane_signature import LaneSignature, parse_lane_signature
from darwin.models.mailbox import (
    DarwinMailboxAddress,
    MailboxCapability,
    MailboxIdentity,
    format_mailbox_address,
)


def register_mailbox(
    registry_hub: RegistryHub,
    mailbox_identity: MailboxIdentity,
) -> MailboxIdentity:
    """Store or replace a mailbox identity by mailbox ID on a RegistryHub."""
    if not isinstance(mailbox_identity, MailboxIdentity):
        raise TypeError("mailbox_identity must be a MailboxIdentity")

    existing = registry_hub.mailboxes.get(mailbox_identity.mailbox_id)
    if (
        existing is not None
        and existing.address.raw != mailbox_identity.address.raw
        and registry_hub.mailbox_address_index.get(existing.address.raw)
        == mailbox_identity.mailbox_id
    ):
        del registry_hub.mailbox_address_index[existing.address.raw]

    registry_hub.mailboxes[mailbox_identity.mailbox_id] = mailbox_identity
    registry_hub.mailbox_address_index[mailbox_identity.address.raw] = (
        mailbox_identity.mailbox_id
    )
    return mailbox_identity


def get_mailbox(
    registry_hub: RegistryHub,
    mailbox_id: str,
) -> MailboxIdentity | None:
    """Return a registered mailbox identity, if present."""
    _validate_required_string(mailbox_id, "mailbox_id")
    return registry_hub.mailboxes.get(mailbox_id)


def resolve_mailbox_address(
    registry_hub: RegistryHub,
    mailbox_address: DarwinMailboxAddress | str,
) -> MailboxIdentity | None:
    """Resolve a DARWIN mailbox address through the RegistryHub address index."""
    address = _mailbox_address(mailbox_address)
    mailbox_id = registry_hub.mailbox_address_index.get(address.raw)
    if mailbox_id is None:
        return None
    return registry_hub.mailboxes.get(mailbox_id)


def list_mailboxes(
    registry_hub: RegistryHub,
    *,
    scope: str | None = None,
    canonical_device_id: str | None = None,
    capability: MailboxCapability | str | None = None,
) -> list[MailboxIdentity]:
    """Return registered mailboxes in deterministic mailbox ID order."""
    _validate_optional_string(scope, "scope")
    _validate_optional_string(canonical_device_id, "canonical_device_id")
    capability_key = _capability_filter_key(capability)

    return [
        mailbox
        for _, mailbox in sorted(registry_hub.mailboxes.items())
        if (scope is None or mailbox.scope == scope)
        and (
            canonical_device_id is None
            or mailbox.canonical_device_id == canonical_device_id
        )
        and (
            capability_key is None
            or any(
                mailbox_capability.capability_id == capability_key
                or mailbox_capability.lane_signature == capability_key
                for mailbox_capability in mailbox.capabilities
            )
        )
    ]


def bind_mailbox_capability(
    registry_hub: RegistryHub,
    mailbox_id: str,
    capability: MailboxCapability,
) -> MailboxIdentity:
    """Bind a registered mailbox to a registered lane signature capability."""
    mailbox = get_mailbox(registry_hub, mailbox_id)
    if mailbox is None:
        raise KeyError(f"mailbox_id is not registered: {mailbox_id}")
    if not isinstance(capability, MailboxCapability):
        raise TypeError("capability must be a MailboxCapability")

    lane_signature = parse_lane_signature(capability.lane_signature).signature
    if lane_signature not in registry_hub.lane_registry:
        raise ValueError(
            "capability lane_signature must be registered before mailbox binding"
        )

    capabilities = [
        existing
        for existing in mailbox.capabilities
        if existing.capability_id != capability.capability_id
    ]
    capabilities.append(capability)
    updated = replace(mailbox, capabilities=tuple(capabilities))
    return register_mailbox(registry_hub, updated)


def mailbox_supports_lane(
    registry_hub: RegistryHub,
    mailbox_id: str,
    lane_signature: LaneSignature | str,
) -> bool:
    """Return whether a registered mailbox has an enabled capability for a lane."""
    mailbox = get_mailbox(registry_hub, mailbox_id)
    if mailbox is None:
        return False

    signature = _lane_signature_key(lane_signature)
    return any(
        capability.enabled and capability.lane_signature == signature
        for capability in mailbox.capabilities
    )


def list_mailbox_capabilities(
    registry_hub: RegistryHub,
    mailbox_id: str,
) -> list[MailboxCapability]:
    """Return mailbox capabilities in deterministic capability ID order."""
    mailbox = get_mailbox(registry_hub, mailbox_id)
    if mailbox is None:
        return []
    return sorted(mailbox.capabilities, key=lambda capability: capability.capability_id)


def make_basic_messaging_mailbox(
    *,
    mailbox_id: str,
    canonical_device_id: str,
    local_name: str,
    scope: str,
    resource: str = "inbox",
    enabled: bool = True,
) -> MailboxIdentity:
    """Return a mailbox identity with a basic_messaging:v1 capability."""
    return MailboxIdentity(
        mailbox_id=mailbox_id,
        canonical_device_id=canonical_device_id,
        local_name=local_name,
        scope=scope,
        address=format_mailbox_address(
            scope=scope,
            mailbox=local_name,
            resource=resource,
        ),
        capabilities=(
            MailboxCapability(
                capability_id="cap_basic_messaging",
                lane_signature="basic_messaging:v1",
                enabled=enabled,
                metadata={"simulator_local": True},
            ),
        ),
        metadata={"simulator_local": True},
    )


def _mailbox_address(mailbox_address: DarwinMailboxAddress | str) -> DarwinMailboxAddress:
    if isinstance(mailbox_address, DarwinMailboxAddress):
        return mailbox_address
    if isinstance(mailbox_address, str):
        from darwin.models.mailbox import parse_mailbox_address

        return parse_mailbox_address(mailbox_address)
    raise TypeError("mailbox_address must be a DarwinMailboxAddress or string")


def _capability_filter_key(capability: MailboxCapability | str | None) -> str | None:
    if capability is None:
        return None
    if isinstance(capability, MailboxCapability):
        return capability.capability_id
    if isinstance(capability, str):
        _validate_required_string(capability, "capability")
        return capability
    raise TypeError("capability must be a MailboxCapability, string, or None")


def _lane_signature_key(lane_signature: LaneSignature | str) -> str:
    if isinstance(lane_signature, LaneSignature):
        return lane_signature.signature
    if isinstance(lane_signature, str):
        return parse_lane_signature(lane_signature).signature
    raise TypeError("lane_signature must be a LaneSignature or string")


def _validate_required_string(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} is required")
    if value.strip() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _validate_optional_string(value: str | None, field_name: str) -> None:
    if value is None:
        return
    _validate_required_string(value, field_name)
