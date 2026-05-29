# DARWIN Identity, Trust, and Authentication Model v0.1

**Project name:** DARWIN  
**Document:** Identity, Trust, and Authentication Model  
**Version:** v0.1  
**Status:** Concept draft / security architecture sketch  
**Related document:** DARWIN Design Dossier v0.1

---

## 1. Purpose

This document defines the first draft of DARWIN’s identity, trust, and authentication model.

The core question is:

```text
How does DARWIN know that a device is really the device it claims to be?
```

DARWIN separates cross-network identity from local network continuity.

A device may need to prove different things at different times:

```text
Across networks:
  I am the same device that was issued this passport.

When moving:
  I am authorized to move from one registry branch to another.

Inside a local network:
  I am still the same active actor that registered earlier.

For packets/checkpoints:
  This message belongs to the current authenticated session.

When suspicious:
  Re-check me more deeply, quarantine me, or reject me.
```

The goal is not to make every packet carry a full passport. The goal is to authenticate heavily at trust boundaries, then preserve continuity cheaply inside a trusted scope.

---

## 2. Core Principle

DARWIN’s authentication model is layered:

```text
Passport layer:
  durable cross-network identity

Move contract layer:
  signed relocation between scopes

Parent attestation layer:
  proof that a hub currently vouches for a child device

Local rolling-auth layer:
  same-network continuity proof

Packet/checkpoint auth layer:
  lightweight ongoing validation
```

One-sentence rule:

```text
A passport proves who you are, a move contract proves where you moved, and rolling local proof proves you are still the same actor inside the current network.
```

---

## 3. Trust Zones

DARWIN should treat different environments as different trust zones.

### 3.1 Global / Federated Trust Zone

This is the broadest trust layer.

Used when:

```text
A device enters a new registry tree.
A device crosses from one administrative scope to another.
A device needs to prove durable identity.
A device is looked up by a high-level registry hub.
```

Primary mechanisms:

```text
Agreement Certificate / Passport
Registry issuer trust
Device public key or equivalent durable identity proof
Revocation lists or status checks
```

---

### 3.2 Registry Scope Trust Zone

This is the trust boundary of a particular Registry Hub or namespace branch.

Used when:

```text
A device joins a local scope.
A device requests a name under that scope.
A device moves between child hubs.
A hub hands summary information upward.
```

Primary mechanisms:

```text
Scope policies
Move contracts
Parent attestations
Local registry table checks
```

---

### 3.3 Local Network Trust Zone

This is the trust zone inside a single active network or hub-managed area.

Used when:

```text
A device is already registered locally.
A hub needs to verify the device is still present.
A device sends checkpoint packets.
A device participates in active logical lanes.
A MAC address or link-layer identity changes suspiciously.
```

Primary mechanisms:

```text
Local session secret
Rolling proof
Challenge-response checks
Packet/checkpoint auth tags
Replay protection
```

---

### 3.4 Suspicion / Quarantine Zone

This is the state for devices or claims that cannot yet be trusted.

Used when:

```text
A device lacks a passport.
A passport is unknown or revoked.
A proof fails.
A duplicate device_id appears.
A MAC address is spoofed.
A device claims a parent role without authorization.
A move conflict occurs.
```

Primary mechanisms:

```text
Quarantine network
Limited capabilities
Forced re-authentication
Registry escalation
Human/admin review
```

---

## 4. Identity Objects

### 4.1 Device ID

The Device ID is the durable identifier for a device.

It should not be trusted merely because a device claims it.

A Device ID should ideally be bound to a cryptographic identity, such as:

```text
A public key fingerprint
A generated UUID tied to a stored keypair
A hardware-secured identity key
A registry-issued durable identifier
```

Example:

```yaml
device_identity:
  device_id: dev_A9F3
  public_key_fingerprint: pkfp_71C92
  identity_created_at: 2026-05-26T12:00:00Z
```

Open design choice:

```text
Should device_id be derived from the device public key, issued by a registry, or generated independently and then bound to a key?
```

---

### 4.2 Device Label

The Device Label is the human-readable name requested by the device or assigned by a hub.

Examples:

```text
my_pc
printer
phone
livingroom_sensor
```

Labels are not durable proof of identity.

A malicious device can claim:

```text
I am printer.
```

DARWIN should respond:

```text
That is only a label request. Prove your device_id and authorization.
```

---

### 4.3 Identity Chain

The Identity Chain is the scoped registry path for a device.

Example:

```text
global.family.david.home.my_pc
```

This is a logical path, not necessarily the physical traffic route.

The Identity Chain may change if a device moves, but the Device ID should remain stable.

---

## 5. Agreement Certificate / Passport

The Agreement Certificate, also called the Passport, is the root trust document for a DARWIN device.

It is created when a device is first approved into a registry scope.

The passport proves:

```text
The device owns or controls a durable device identity.
A Registry Hub approved this identity into a scope.
The device and Registry Hub both agreed to the registration.
The device has specific permissions and restrictions.
```

Example:

```yaml
agreement_certificate:
  certificate_id: cert_123
  device_id: dev_A9F3
  canonical_label: my_pc
  issuing_registry_hub: hub_david_devices_001
  issued_scope: global.family.david.devices
  issued_at: 2026-05-26T12:00:00Z
  expires_at: null
  device_public_key: DEVICE_PUBLIC_KEY
  registry_public_key: REGISTRY_PUBLIC_KEY
  permissions:
    can_register_locally: true
    can_move_between_scopes: true
    can_host_services: false
    can_act_as_parent_hub: false
  constraints:
    allowed_scopes:
      - global.family.david.*
    denied_scopes:
      - global.family.david.secure_lab.*
  signatures:
    device: DEVICE_SIGNATURE
    registry_hub: REGISTRY_SIGNATURE
```

---

## 6. Passport Use Cases

A passport is used for heavy authentication at meaningful trust boundaries.

Use passport verification when:

```text
A device first joins a network.
A device joins a new Registry Hub.
A device crosses registry trees.
A device requests long-lived permissions.
A local rolling proof fails and escalation is required.
A hub detects spoofing or identity conflict.
A device wants to host services or act as a parent.
```

Do not require full passport verification for every normal packet.

That would make the network expensive, chatty, and brittle.

---

## 7. Issuer Trust

A passport is only useful if the issuing Registry Hub is trusted.

A hub verifying a passport should ask:

```text
Do I trust this issuer directly?
Do I trust an ancestor of this issuer?
Can I discover a trust path to this issuer?
Has this issuer been revoked or demoted?
Is this issuer authorized to create passports for this scope?
```

Example issuer record:

```yaml
trusted_issuer:
  registry_hub_id: hub_david_devices_001
  scope_authority: global.family.david.devices
  public_key: REGISTRY_PUBLIC_KEY
  trust_level: local_family_authority
  valid_from: 2026-05-26T00:00:00Z
  valid_until: null
  status: active
```

Potential trust levels:

```text
self
local_parent
regional_parent
federated_peer
global_anchor
temporary_guest_authority
revoked
unknown
```

---

## 8. Move Contracts

A Move Contract is a signed record that says a device changed attachment or registry scope.

The Move Contract references the original passport.

It acts like a passport stamp.

Example:

```yaml
move_contract:
  move_id: move_456
  certificate_id: cert_123
  device_id: dev_A9F3
  from_scope: global.family.david.home
  to_scope: global.family.david.office
  old_attachment: hub_home_001
  new_attachment: hub_office_007
  timestamp: 2026-05-26T12:05:00Z
  move_nonce: nonce_918273
  movement_reason: roaming
  signatures:
    device: DEVICE_SIGNATURE
    new_registry_hub: NEW_HUB_SIGNATURE
    old_registry_hub: OPTIONAL_OLD_HUB_SIGNATURE
```

A hub should reject a move claim if:

```text
The passport is missing or invalid.
The device cannot sign the move.
The new hub is not authorized to accept the device.
The move conflicts with an active registration elsewhere.
The same move nonce was already used.
The move is stale or replayed.
```

---

## 9. Parent Attestations

A Parent Attestation is a short-lived statement by a hub that it currently vouches for a child device.

It helps prove that a device is not merely pretending to sit behind a parent.

Example:

```yaml
parent_attestation:
  attestation_id: attest_789
  child_device_id: dev_A9F3
  parent_hub_id: hub_home_001
  scope: global.family.david.home
  session_epoch: epoch_8821
  valid_from: 2026-05-26T12:00:00Z
  valid_until: 2026-05-26T12:10:00Z
  permitted_roles:
    can_send_packets: true
    can_receive_packets: true
    can_act_as_parent_hub: false
  signature:
    parent_hub: PARENT_SIGNATURE
```

Parent Attestations should be short-lived.

They are useful for:

```text
local access control
child-device validation
hub-to-hub verification
movement handoff
anti-impersonation checks
```

---

## 10. Local Session Authentication

Once a device has been admitted to a local network, the local hub can create a local session.

The local session is cheaper than repeatedly checking the full passport.

Example local session:

```yaml
local_auth_session:
  session_id: sess_8821
  device_id: dev_A9F3
  hub_id: hub_home_001
  scope: global.family.david.home
  created_at: 2026-05-26T12:00:00Z
  expires_at: 2026-05-26T18:00:00Z
  auth_method: rolling_cmac_or_hmac
  current_counter: 1042
  state: active
```

The local session answers:

```text
Is this still the same authenticated device inside this network?
```

It does not replace the passport.

It reduces the need to repeatedly use it.

---

## 11. Rolling Proof Mode

Rolling Proof Mode is a local continuity mechanism.

It can be used to prevent a device from sneaking into a network by spoofing another device’s MAC address, label, or local address.

The local hub may ask the device to prove it still knows the local session secret.

Important rule:

```text
The static secret should never be revealed to a verifier.
The device should only reveal proof generated from the secret.
```

Bad pattern:

```text
Hub asks device for static key.
Device sends static key.
Verifier learns reusable secret.
```

Better pattern:

```text
Hub sends challenge.
Device computes proof using local secret.
Hub or identity authority verifies proof.
Secret never leaves trusted storage.
```

Example challenge:

```yaml
local_auth_challenge:
  challenge_id: chal_001
  device_id: dev_A9F3
  hub_id: hub_home_001
  scope: global.family.david.home
  session_epoch: epoch_8821
  counter: 1043
  nonce: RANDOM_NONCE
  requested_capability: send_checkpoint
```

Example proof:

```yaml
local_auth_proof:
  challenge_id: chal_001
  device_id: dev_A9F3
  counter: 1043
  proof_method: AES_CMAC_STYLE_OR_HMAC_STYLE
  proof: PROOF_VALUE
```

Conceptual calculation:

```text
proof = MAC(local_session_secret,
            device_id |
            hub_id |
            scope |
            session_epoch |
            counter |
            nonce |
            requested_capability)
```

This proof should be bound to context so it cannot be replayed somewhere else.

---

## 12. Static Secret vs Session Secret

There are two different secret types to consider.

### 12.1 Long-Term Device Secret

A long-term device secret may be used for constrained devices that cannot support full public-key authentication.

Risks:

```text
If the identity server leaks the secret database, devices can be impersonated.
If a hub learns the secret, the hub can impersonate the device.
If the secret is reused across scopes, replay risk increases.
```

Rule:

```text
Avoid exposing long-term static secrets to ordinary hubs.
```

---

### 12.2 Local Session Secret

A local session secret is derived or negotiated after the device has been admitted.

It is scoped to:

```text
device_id
hub_id
network_scope
session_epoch
expiration window
```

If compromised, it should only affect a local session, not the device’s global identity.

Preferred pattern:

```text
Use passport authentication to establish a local session.
Derive a local session secret.
Use the local session secret for rolling proofs and packet/checkpoint auth tags.
Expire and rotate it regularly.
```

---

## 13. Packet and Checkpoint Auth Tags

Packets and checkpoint messages should carry lightweight authenticity markers.

They do not need to contain the full passport.

Example checkpoint with auth tag:

```yaml
checkpoint_packet:
  checkpoint_id: cp_001
  device_id: dev_A9F3
  session_id: sess_8821
  hub_id: hub_home_001
  state: online
  counter: 1044
  timestamp: 2026-05-26T12:06:00Z
  payload:
    lane_count: 3
    battery_level: 91
  auth_tag: AUTH_TAG
```

Conceptual auth tag:

```text
auth_tag = MAC(local_session_secret,
               packet_header |
               counter |
               timestamp |
               payload_hash)
```

Auth tags help detect:

```text
packet tampering
replay attacks
forged checkpoints
spoofed continuity
unauthorized local presence
```

---

## 14. Replay Protection

Rolling proofs must prevent old valid messages from being reused.

DARWIN can use:

```text
monotonic counters
nonces
short time windows
session epochs
hub-specific context
scope-specific context
capability-specific context
```

A hub should reject a proof if:

```text
The counter is old.
The nonce was already used.
The session epoch is expired.
The proof was generated for another hub.
The proof was generated for another scope.
The requested capability does not match the proof context.
```

Example replay rejection:

```yaml
verification_result:
  valid: false
  reason: stale_counter
  action: re_challenge_or_quarantine
```

---

## 15. MAC Spoofing Defense

DARWIN should not treat MAC addresses as identity.

A MAC address may be useful as a routing hint, but it should not be trusted as proof.

Attack pattern:

```text
Attacker observes trusted device MAC.
Attacker spoofs the MAC.
Attacker tries to receive network access as the trusted device.
```

DARWIN response:

```text
The MAC matches, but the device must pass local rolling proof.
If it cannot prove possession of the session secret or passport key, it is rejected or quarantined.
```

Example decision:

```yaml
mac_spoof_check:
  claimed_mac: AA:BB:CC:DD:EE:FF
  claimed_device_id: dev_A9F3
  rolling_proof_valid: false
  passport_recheck_valid: false
  action: quarantine
```

Policy rule:

```text
MAC address is a transport clue, not an identity credential.
```

---

## 16. Parent Impersonation Defense

DARWIN must prevent devices from pretending to be parent hubs.

Attack pattern:

```text
A malicious device claims to be a parent hub.
It tries to vouch for other devices.
It attempts to forward or intercept traffic.
```

Required checks:

```text
Does this actor have a passport permitting parent or hub behavior?
Does it have a valid hub certificate?
Is it authorized for this scope?
Can it sign Parent Attestations with a trusted hub key?
Is the claimed child relationship expected?
```

Example rejection:

```yaml
parent_role_check:
  actor_device_id: dev_MALICIOUS
  requested_role: parent_hub
  passport_allows_parent_role: false
  trusted_hub_certificate_present: false
  action: reject_parent_claim
```

---

## 17. Trust Escalation Rules

DARWIN should not perform expensive verification for every small action.

Instead, trust should escalate when risk increases.

### 17.1 Normal Local Activity

Use:

```text
local session auth
rolling proof
packet/checkpoint auth tags
```

---

### 17.2 Suspicious Local Activity

Triggers:

```text
failed rolling proof
unexpected MAC change
duplicate local address
impossible movement
unusual packet pattern
stale checkpoint
counter reset
```

Response:

```text
pause local access
force re-challenge
require passport proof
possibly quarantine
```

---

### 17.3 Registry Boundary Crossing

Triggers:

```text
new Registry Hub
new scope
network branch change
federated tree crossing
```

Response:

```text
verify passport
create move contract
ask registry history
issue new local session
```

---

### 17.4 Identity Conflict

Triggers:

```text
two active devices claim same device_id
two hubs claim current attachment for same device
passport fork detected
move contract conflict
```

Response:

```text
freeze affected lanes
ask previous registry authority
query witness hubs
quarantine both claims if needed
require deeper proof
```

---

## 18. Revocation

DARWIN needs a way to invalidate passports, hubs, sessions, and permissions.

Revocation targets:

```text
device passport
hub authority certificate
local session
move contract
parent attestation
capability grant
```

Example revocation record:

```yaml
revocation_record:
  revoked_id: cert_123
  revoked_type: agreement_certificate
  device_id: dev_A9F3
  revoked_by: hub_david_devices_001
  revoked_at: 2026-05-26T13:00:00Z
  reason: suspected_key_compromise
  signature:
    registry_hub: REGISTRY_SIGNATURE
```

A hub checking a device should ask:

```text
Is the passport valid?
Is the issuer still trusted?
Has the device been revoked?
Has the current local session been revoked?
Are there scope-specific restrictions?
```

---

## 19. Quarantine

Quarantine is a restricted state for devices that are not trusted enough for full access.

Quarantined devices may be allowed to:

```text
request identity recovery
present a passport
receive limited captive-portal-style instructions
contact a registry authority
sync time
perform diagnostic handshake
```

Quarantined devices should not be allowed to:

```text
send normal traffic
host services
act as a parent hub
forward packets for others
claim names in the normal namespace
join active lanes
```

Example quarantine record:

```yaml
quarantine_record:
  claimed_device_id: dev_A9F3
  local_observed_mac: AA:BB:CC:DD:EE:FF
  reason: rolling_proof_failed
  allowed_actions:
    - present_passport
    - request_recovery
    - sync_time
  denied_actions:
    - send_normal_traffic
    - act_as_parent_hub
    - host_services
```

---

## 20. Capability-Based Permissions

A DARWIN passport or local session should describe what a device is allowed to do.

Capabilities might include:

```text
can_register_locally
can_request_routes
can_send_packets
can_receive_packets
can_host_services
can_act_as_parent_hub
can_issue_parent_attestations
can_create_child_scope
can_use_high_frequency_checkpoints
can_request_lane_preservation
```

Example:

```yaml
capabilities:
  can_register_locally: true
  can_request_routes: true
  can_send_packets: true
  can_receive_packets: true
  can_host_services: false
  can_act_as_parent_hub: false
  can_issue_parent_attestations: false
  can_request_lane_preservation: true
```

This prevents every authenticated device from automatically gaining every possible network role.

---

## 21. Authentication Flow: New Device Joins Network

```text
1. Device connects to local hub.
2. Device claims or requests device_label.
3. Hub asks for passport or begins first-registration flow.
4. Device proves control of passport key or registration secret.
5. Hub validates issuer trust and scope permissions.
6. Hub checks revocation status.
7. Hub checks local namespace conflicts.
8. Hub admits device or assigns temporary label.
9. Hub creates local session.
10. Device and hub establish local rolling-auth state.
11. Hub registers local device state and optionally hands summary upward.
```

Result:

```yaml
join_result:
  device_id: dev_A9F3
  assigned_label: my_pc
  scope: global.family.david.home
  local_session_id: sess_8821
  checkpoint_mode: tier_2_mobile
  state: online
```

---

## 22. Authentication Flow: Known Device Rejoins Same Network

```text
1. Device reconnects to known local hub.
2. Device presents device_id and prior session reference if available.
3. Hub checks whether prior session is still valid.
4. If valid, hub sends rolling challenge.
5. Device returns proof.
6. If proof succeeds, session resumes or rotates.
7. If proof fails, hub escalates to passport verification.
```

Decision:

```text
Valid rolling proof    → resume local access
Expired session        → verify passport and create new session
Failed proof           → re-challenge, passport check, or quarantine
Revoked passport       → reject
```

---

## 23. Authentication Flow: MAC Spoof Attempt

```text
1. Attacker spoofs MAC of trusted device.
2. Hub sees familiar MAC but unexpected behavior or new link context.
3. Hub requests rolling proof for claimed device_id.
4. Attacker cannot generate proof.
5. Hub blocks normal access.
6. Hub may notify registry and quarantine the claim.
```

Result:

```yaml
security_event:
  event_type: mac_spoof_detected
  claimed_device_id: dev_A9F3
  claimed_mac: AA:BB:CC:DD:EE:FF
  proof_valid: false
  action: quarantine
```

---

## 24. Authentication Flow: Device Moves Between Networks

```text
1. Device disconnects from Hub A.
2. Hub A marks device as in_transit.
3. Hub A freezes or pauses active local sessions and lanes.
4. Device appears at Hub B.
5. Device presents passport.
6. Hub B verifies passport, issuer trust, and revocation.
7. Hub B asks registry chain for device history.
8. Hub B creates Move Contract.
9. Registry confirms transition or flags conflict.
10. Hub B creates new local session.
11. Active lanes may be rerouted and resumed.
```

Important distinction:

```text
The passport handles cross-network identity.
The new local session handles continuity inside the new network.
```

---

## 25. Authentication Flow: Parent Hub Claim

```text
1. Actor claims it can act as a parent hub.
2. Verifying hub checks actor passport or hub certificate.
3. Verifying hub checks scope authority.
4. Verifying hub checks parent capability.
5. Actor signs a challenge using hub-authorized key.
6. If valid, actor may issue Parent Attestations.
7. If invalid, parent role is rejected.
```

Result:

```yaml
parent_claim_result:
  actor_id: hub_or_device_X
  requested_scope: global.family.david.home.children
  parent_role_valid: false
  reason: missing_parent_capability
  action: reject
```

---

## 26. Trust State Machine

A device might move through these trust states:

```text
unknown
claiming_identity
passport_verified
locally_authenticated
active
in_transit
awaiting_reverification
quarantined
revoked
rejected
```

Example transition flow:

```text
unknown
→ claiming_identity
→ passport_verified
→ locally_authenticated
→ active
→ in_transit
→ passport_verified
→ locally_authenticated
→ active
```

Suspicious flow:

```text
active
→ rolling_proof_failed
→ awaiting_reverification
→ passport_failed
→ quarantined
```

---

## 27. Security Events

DARWIN hubs should log and possibly propagate security events.

Possible events:

```text
passport_verification_failed
issuer_unknown
revoked_passport_presented
rolling_proof_failed
packet_auth_failed
checkpoint_auth_failed
mac_spoof_suspected
parent_impersonation_attempt
duplicate_device_id_active
move_contract_conflict
stale_counter_detected
replay_detected
quarantine_started
quarantine_released
```

Example event:

```yaml
security_event:
  event_id: sec_001
  event_type: rolling_proof_failed
  device_id: dev_A9F3
  hub_id: hub_home_001
  scope: global.family.david.home
  timestamp: 2026-05-26T12:10:00Z
  severity: medium
  action_taken: forced_passport_recheck
```

---

## 28. Privacy Considerations

DARWIN identity history could become sensitive.

A device’s movement history may reveal:

```text
where it has been
which networks it uses
which hubs it trusts
what services it hosts
when it is active or inactive
```

Privacy questions:

```text
How much movement history should be visible to ordinary hubs?
Should high-level registries store full histories or summaries?
Can devices request private or minimal registration?
Can aliases hide labels while preserving device_id continuity?
Can local networks use pseudonymous session identifiers?
```

Possible privacy approach:

```text
Local hubs see local details.
Parent hubs see summarized identity state.
Federated peers see only enough to verify legitimacy.
Traffic hubs see route necessities, not full identity history.
```

---

## 29. Threat Model Draft

DARWIN should consider at least these threats:

```text
MAC spoofing
Device ID spoofing
Label squatting
Replay attacks
Stolen local session secrets
Stolen passports
Compromised Registry Hub
Malicious Traffic Hub
Parent hub impersonation
Move contract forgery
Duplicate active identity claims
Checkpoint forgery
Lane hijacking
Revocation bypass
Registry history poisoning
Denial of service through fake registrations
```

For each threat, later documents should define:

```text
Detection method
Prevention method
Recovery path
Logging requirements
Escalation rules
```

---

## 30. Algorithm Placeholders

This document does not lock final cryptographic algorithms.

Possible mechanisms include:

```text
Public-key signatures for passports and move contracts
HMAC-style message authentication for packet/checkpoint tags
AES-CMAC-style proofs for constrained local devices
Key derivation for local session secrets
Counters, nonces, timestamps, and epochs for replay protection
```

Final algorithm choice should consider:

```text
security
implementation simplicity
IoT compatibility
hardware acceleration
library availability
side-channel risks
key rotation
interoperability
```

Rule for future implementation:

```text
Use well-reviewed standard cryptographic constructions rather than custom cryptography.
```

---

## 31. Minimal Viable Trust Model for Simulator

The first simulator does not need production cryptography.

It can model trust using symbolic values.

Example simulator objects:

```yaml
simulated_passport:
  certificate_id: cert_123
  device_id: dev_A9F3
  issuer: hub_home_001
  valid: true

simulated_local_session:
  session_id: sess_8821
  device_id: dev_A9F3
  rolling_counter: 1042
  valid: true
```

Simulator checks:

```text
Does the device have a passport?
Is the issuer trusted?
Is the passport revoked?
Does the move contract reference the passport?
Does the local proof match the expected symbolic token?
Does the counter increase?
```

The simulator should test behavior first, cryptography later.

---

## 32. Open Questions

### Device Identity

- Should device_id be derived from a public key?
- Should devices be allowed to rotate identity keys?
- How does a device recover from lost keys?
- Can one physical device hold multiple DARWIN identities?

### Passport Authority

- Who is allowed to issue first passports?
- Can local/private networks issue passports recognized only locally?
- How are passport issuers discovered?
- How are issuer trust chains represented?

### Local Rolling Proof

- Should rolling proof use counter-based, time-based, challenge-based, or hybrid validation?
- Should the verifier be the local hub or the identity server?
- How often should rolling proof be required?
- What happens if a device sleeps and misses proof windows?

### IoT Constraints

- Can tiny devices support public-key signatures?
- Should constrained devices use symmetric secrets instead?
- Can a trusted parent hub speak for sleepy devices?
- How does the system prevent parent hubs from lying about sleepy children?

### Revocation

- How quickly must revocation propagate?
- Can a device operate temporarily if revocation status is unreachable?
- Are revocation records stored globally, locally, or both?
- How does revocation interact with offline networks?

### Privacy

- How much movement history should be retained?
- Can devices hide labels from high-level registries?
- Can traffic hubs route without knowing human-readable identity chains?
- Can local sessions use pseudonymous handles?

### Compromised Hubs

- How is a malicious Registry Hub detected?
- How is trust in a hub revoked?
- What happens to devices whose passports were issued by a revoked hub?
- Can another hub re-issue or rescue valid devices?

---

## 33. Working Summary

DARWIN’s trust model should use heavy proof at borders and cheap proof inside the walls.

The passport proves durable identity across networks. The move contract proves authorized relocation. The parent attestation proves current hub-child relationship. The local rolling proof prevents spoofed devices from hiding behind MAC addresses or old registrations. Packet and checkpoint auth tags keep ongoing traffic tied to the current authenticated session.

The central security rule is:

```text
Never trust a claimed name, address, MAC, or path by itself. Trust only verified continuity from a known identity through an authorized scope.
```

Or in travel terms:

```text
The passport gets the device across the border. The local session badge keeps it valid inside the building. The rolling proof keeps anyone else from borrowing the jacket and pretending to be the traveler.
```

