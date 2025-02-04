import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

from eth_typing import ChecksumAddress, HexStr
from eth_utils import add_0x_prefix, to_checksum_address
from ethproto.wrappers import ETHWrapper, get_provider

from . import abis
from .roles import get_registry


class BaseEventStream:
    ABI = None

    def __init__(self, contract_address, provider=None):
        self.contract_address = contract_address
        self._event_stream = None

        if provider is None:
            provider = get_provider("w3")
        self.provider = provider

    def _get_contract_wrapper(self):
        contract = self.provider.w3.eth.contract(address=self.contract_address, abi=self.ABI)
        return ETHWrapper.connect(contract)

    def _get_events(self, event_name):
        contract_wrapper = self._get_contract_wrapper()
        return self.provider.get_events(contract_wrapper, event_name)

    @property
    def stream(self):
        if self._event_stream is None:
            self._load_stream()
        return self._event_stream


class AccessControlEventStream(BaseEventStream):
    ABI = abis.OZ_ACCESS_CONTROL

    def _load_stream(self):
        roles_granted = self._get_events("RoleGranted")
        roles_revoked = self._get_events("RoleRevoked")
        # TODO: admin_changes = self.provider.get_events(contract_wrapper, "RoleAdminChanged")

        event_stream = []
        for event in roles_granted + roles_revoked:
            event_stream.append(
                {
                    "role": get_registry().get("0x" + event.args.role.hex()),
                    "subject": event.args.account,
                    "requester": event.args.sender,
                    "order": (event.blockNumber, event.logIndex),
                    "event": event.event,
                }
            )
        self._event_stream = sorted(event_stream, key=lambda e: (e["role"].hash, e["order"]))

    @property
    def snapshot(self):
        snapshot = defaultdict(set)
        for role, events in itertools.groupby(self.stream, key=lambda e: e["role"].hash):
            for event in events:
                if event["event"] == "RoleGranted":
                    snapshot[role].add(event["subject"])
                elif event["event"] == "RoleRevoked":
                    try:
                        snapshot[role].remove(event["subject"])
                        if not snapshot[role]:
                            snapshot.pop(role)
                    except KeyError:
                        raise RuntimeError(
                            f"WARNING: can't remove ungranted role {role} from {event['subject']}"
                        )
                else:
                    raise RuntimeError(f"Unexpected event {event.name} for role {role}")
        return [
            {"role": get_registry().get(role), "members": list(members)} for role, members in snapshot.items()
        ]


@dataclass
class AMRole:
    label: str
    id: int = None
    guardian: int = 0
    admin: int = 0

    # Address -> {selectors}
    targets: dict[ChecksumAddress, set[HexStr]] = None

    members: set[ChecksumAddress] = None

    def __post_init__(self):
        if self.targets is None:
            self.targets = defaultdict(set)
        if self.members is None:
            self.members = set()

    def __str__(self):
        return f"{self.label} ({self.id})"

    def as_dict(self):
        return {
            "label": self.label,
            "id": self.id,
            "guardian": self.guardian,
            "admin": self.admin,
            "members": list(self.members),
            "targets": {k: list(v) for k, v in self.targets.items()},
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            label=data["label"],
            id=data["id"],
            guardian=data["guardian"],
            admin=data["admin"],
            members=set(data["members"]),
            targets={k: set(v) for k, v in data["targets"].items()},
        )


@dataclass
class AMOperation:
    op: Literal[
        "grant_role", "revoke_role", "change_guardian", "change_admin", "change_label", "update_target"
    ]
    role: AMRole
    args: dict

    def as_dict(self):
        return {"op": self.op, "role": self.role.id, "args": self.args}


class AccessManagerEventStream(BaseEventStream):
    ABI = abis.OZ_ACCESS_MANAGER

    ADMIN_ROLE = AMRole("ADMIN_ROLE", id=0, guardian=0, admin=0)
    PUBLIC_ROLE = AMRole("PUBLIC_ROLE", id=2**64 - 1, guardian=0, admin=0)

    def _load_stream(self):
        roles_granted = self._get_events("RoleGranted")
        roles_revoked = self._get_events("RoleRevoked")
        guardian_changes = self._get_events("RoleGuardianChanged")
        admin_changes = self._get_events("RoleAdminChanged")
        labels = self._get_events("RoleLabel")
        targets = self._get_events("TargetFunctionRoleUpdated")

        event_stream = [
            {
                "event": e.event,
                "args": e.args,
                "order": (e.blockNumber, e.logIndex),
            }
            for e in roles_granted + roles_revoked + guardian_changes + admin_changes + labels + targets
        ]

        self._event_stream = sorted(event_stream, key=lambda e: e["order"])

    @classmethod
    def initial_role_states(cls):
        return {
            cls.ADMIN_ROLE.id: cls.ADMIN_ROLE,
            cls.PUBLIC_ROLE.id: cls.PUBLIC_ROLE,
        }

    @property
    def snapshot(self):
        """Returns a snapshot of the current permissions setup.

        The snapshot is a dict with role ids as keys and AMRole instances as values.
        """
        snapshot = dict(self.initial_role_states())
        for role_id, events in itertools.groupby(self.stream, key=lambda e: e["args"].roleId):
            if role_id not in snapshot:
                snapshot[role_id] = AMRole("", id=role_id)
            for event in events:
                if event["event"] == "RoleGranted":
                    # RoleGranted(uint64 indexed roleId, address indexed account, uint32 delay, uint48 since, bool newMember);  # noqa
                    # TODO: take delay and since into account
                    snapshot[role_id].members.add(to_checksum_address(event["args"].account))
                elif event["event"] == "RoleRevoked":
                    # RoleRevoked(uint64 indexed roleId, address indexed account)
                    snapshot[role_id].members.remove(to_checksum_address(event["args"].account))
                elif event["event"] == "RoleGuardianChanged":
                    # RoleGuardianChanged(uint64 indexed roleId, uint64 indexed guardian)
                    snapshot[role_id].guardian = event["args"].guardian
                elif event["event"] == "RoleAdminChanged":
                    # RoleAdminChanged(uint64 indexed roleId, uint64 indexed admin)
                    snapshot[role_id].admin = event["args"].admin
                elif event["event"] == "RoleLabel":
                    # RoleLabel(uint64 indexed roleId, string label)
                    snapshot[role_id].label = event["args"].label
                elif event["event"] == "TargetFunctionRoleUpdated":
                    # TargetFunctionRoleUpdated(address indexed target, bytes4 selector, uint64 indexed roleId)  # noqa
                    snapshot[role_id].targets[to_checksum_address(event["args"].target)].add(
                        add_0x_prefix(HexStr(event["args"].selector.hex()))
                    )
                else:
                    raise RuntimeError(f"Unexpected event {event.name} for role {role_id}")
        return snapshot

    def compare(self, snapshot):
        """Compares the current snapshot with the given one. Returns the differences.

        snapshot must be a snapshot previously obtained from the snapshot property.

        The differences are returned as a series of operations to apply to bring the current state to the
        snapshot state.
        """
        current = self.snapshot
        differences = []

        for role_id, current_role in current.items():
            snapshot_role = snapshot.get(
                role_id,
                AMRole(
                    # Labels cannot be removed, but we'll consider an empty label for an extra role as a match
                    label=(
                        "" if role_id not in (self.ADMIN_ROLE.id, self.PUBLIC_ROLE.id) else current_role.label
                    ),
                    id=role_id,
                    # By default every target function is restricted to the `ADMIN_ROLE`
                    guardian=self.ADMIN_ROLE.id,
                    admin=self.ADMIN_ROLE.id,
                    members=set(),
                    targets={},
                ),
            )

            if current_role.label != snapshot_role.label:
                differences.append(AMOperation("change_label", current_role, {"label": snapshot_role.label}))
            if current_role.admin != snapshot_role.admin:
                differences.append(AMOperation("change_admin", current_role, {"admin": snapshot_role.admin}))
            if current_role.guardian != snapshot_role.guardian:
                differences.append(
                    AMOperation("change_guardian", current_role, {"guardian": snapshot_role.guardian})
                )
            if current_role.members != snapshot_role.members:
                for member in current_role.members - snapshot_role.members:
                    differences.append(AMOperation("revoke_role", current_role, {"account": member}))
                for member in snapshot_role.members - current_role.members:
                    differences.append(AMOperation("grant_role", current_role, {"account": member}))

            for target, selectors in current_role.targets.items():
                if target not in snapshot_role.targets:
                    # By default every target function is restricted to the `ADMIN_ROLE`
                    differences.append(
                        AMOperation(
                            "update_target", self.ADMIN_ROLE, {"target": target, "selectors": selectors}
                        )
                    )
                else:
                    extra = selectors - snapshot_role.targets[target]
                    missing = snapshot_role.targets[target] - selectors
                    if extra:
                        differences.append(
                            AMOperation(
                                "update_target", self.ADMIN_ROLE, {"target": target, "selectors": extra}
                            )
                        )
                    if missing:
                        differences.append(
                            AMOperation(
                                "update_target", current_role, {"target": target, "selectors": missing}
                            )
                        )

        return differences
