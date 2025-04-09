import itertools
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Literal, Optional, Set

from eth_typing import ChecksumAddress, HexStr
from eth_utils import add_0x_prefix, to_checksum_address

MAX_UINT64 = 2**64 - 1


@dataclass(frozen=True)
class Role:
    id: int
    label: str = None
    grant_delay: timedelta = timedelta(0)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Role):
            return False
        return self.id == other.id

    def as_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "grant_delay": self.grant_delay,
        }

    def from_dict(data: dict) -> "Role":
        return Role(
            id=data["id"],
            label=data["label"],
            grant_delay=(
                timedelta(seconds=data["grant_delay"])
                if not isinstance(data["grant_delay"], timedelta)
                else data["grant_delay"]
            ),
        )


@dataclass(frozen=True)
class Target:
    address: ChecksumAddress
    closed: bool = False
    admin_delay: timedelta = timedelta(0)

    def __hash__(self):
        return hash(self.address)

    def __eq__(self, other):
        if not isinstance(other, Target):
            return False
        return self.address == other.address

    def as_dict(self):
        return {
            "address": self.address,
            "closed": self.closed,
            "admin_delay": self.admin_delay,
        }

    def from_dict(data: dict) -> "Target":
        return Target(
            address=data["address"],
            closed=data["closed"],
            admin_delay=timedelta(seconds=data["admin_delay"]),
        )


@dataclass(frozen=True)
class RoleMember:
    address: ChecksumAddress
    execution_delay: timedelta = timedelta(0)

    def __hash__(self):
        return hash((self.address))

    def __eq__(self, other):
        if not isinstance(other, RoleMember):
            return False
        return self.address == other.address

    def as_dict(self):
        return {
            "address": self.address,
            "execution_delay": self.execution_delay,
        }


@dataclass(frozen=True)
class SelectorRole:
    role: Role
    selector: HexStr

    def __hash__(self):
        return hash((self.role, self.selector))

    def __eq__(self, other):
        if not isinstance(other, SelectorRole):
            return False
        return self.role == other.role and self.selector == other.selector


class AccessManager:
    roles: Dict[int, Role]  # id -> Role
    targets: Dict[ChecksumAddress, Target]  # address -> Target

    role_members: Dict[int, Set[RoleMember]]  # role_id -> Members
    role_admins: Dict[int, Role]  # role_id -> Admin
    role_guardians: Dict[int, Role]  # role_id -> Guardian

    target_allowed_roles: Dict[ChecksumAddress, Set[SelectorRole]]  # target -> Selector Allowed Role

    ADMIN_ROLE = Role(label="ADMIN_ROLE", id=0)
    PUBLIC_ROLE = Role(label="PUBLIC_ROLE", id=MAX_UINT64)

    def __init__(self):
        self.roles = {
            self.ADMIN_ROLE.id: self.ADMIN_ROLE,
            self.PUBLIC_ROLE.id: self.PUBLIC_ROLE,
        }
        self.targets = {}
        self.role_members = defaultdict(set)
        self.role_admins = {}
        self.role_guardians = {}
        self.target_allowed_roles = defaultdict(set)

    @classmethod
    def from_events(cls, events: List[dict]) -> "AccessManager":
        """Loads a current state access manager as defined by the events."""
        am = cls()
        for role_id, events in itertools.groupby(events, key=lambda e: e["args"].roleId):
            for event in events:
                if event["event"] == "RoleGranted":
                    # RoleGranted(uint64 indexed roleId, address indexed account, uint32 delay, uint48 since, bool newMember);  # noqa
                    am.grant_role(
                        Role(role_id),
                        to_checksum_address(event["args"].account),
                        timedelta(seconds=event["args"].delay),
                    )
                elif event["event"] == "RoleRevoked":
                    # RoleRevoked(uint64 indexed roleId, address indexed account)
                    am.revoke_role(Role(role_id), to_checksum_address(event["args"].account))
                elif event["event"] == "RoleGuardianChanged":
                    # RoleGuardianChanged(uint64 indexed roleId, uint64 indexed guardian)
                    am.set_role_guardian(Role(role_id), Role(event["args"].guardian))
                elif event["event"] == "RoleAdminChanged":
                    # RoleAdminChanged(uint64 indexed roleId, uint64 indexed admin)
                    am.set_role_admin(Role(role_id), Role(event["args"].admin))
                elif event["event"] == "RoleLabel":
                    # RoleLabel(uint64 indexed roleId, string label)
                    am.label_role(Role(role_id), event["args"].label)
                elif event["event"] == "TargetFunctionRoleUpdated":
                    # TargetFunctionRoleUpdated(address indexed target, bytes4 selector, uint64 indexed roleId)  # noqa
                    am.set_target_function_role(
                        am.get_target(to_checksum_address(event["args"].target)),
                        {add_0x_prefix(HexStr(event["args"].selector.hex()))},
                        Role(role_id),
                    )
                elif event["event"] == "RoleGrantDelayChanged":
                    # RoleGrantDelayChanged(uint64 indexed roleId, uint32 delay, uint48 since);
                    am.set_grant_delay(Role(role_id), timedelta(seconds=event["args"].delay))
                elif event["event"] == "TargetClosed":
                    # TargetClosed(address indexed target, bool closed)
                    am.set_target_closed(
                        am.get_target(to_checksum_address(event["args"].target)), event["args"].closed
                    )
                elif event["event"] == "TargetAdminDelayUpdated":
                    # TargetAdminDelayUpdated(address indexed target, uint32 delay, uint48 since)
                    am.set_target_admin_delay(
                        am.get_target(to_checksum_address(event["args"].target)),
                        timedelta(seconds=event["args"].delay),
                    )
                else:
                    raise RuntimeError(f"Unexpected event {event.name} for role {role_id}")
        return am

    def get_role(self, role_id: int) -> Optional[Role]:
        return self.roles.get(role_id)

    def get_role_members(self, role: Role) -> Set[RoleMember]:
        return self.role_members.get(role.id, set())

    def get_role_admin(self, role: Role) -> Optional[Role]:
        return self.role_admins.get(role.id, self.ADMIN_ROLE)

    def get_role_guardian(self, role: Role) -> Optional[Role]:
        return self.role_guardians.get(role.id, self.ADMIN_ROLE)

    def get_target(self, address: ChecksumAddress) -> Optional[Target]:
        return self.targets.get(address, Target(address, False, timedelta(0)))

    def get_target_allowed_role(self, address: ChecksumAddress, selector: HexStr) -> Optional[Role]:
        for selector_role in self.target_allowed_roles.get(address, set()):
            if selector_role.selector == selector:
                return selector_role.role

    def get_all_target_selectors(self, target: Target) -> Set[HexStr]:
        return {
            selector_role.selector for selector_role in self.target_allowed_roles.get(target.address, set())
        }

    def get_all_role_targets(self, role: Role) -> Dict[Target, Set[HexStr]]:
        ret = {}
        for target_address, selector_roles in self.target_allowed_roles.items():
            selectors = {
                selector_role.selector for selector_role in selector_roles if selector_role.role == role
            }
            if selectors:
                ret[self.get_target(target_address)] = selectors
        return ret

    def label_role(self, role: Role, label: str):
        if role.id in self.roles:
            if self.roles[role.id].label != label:
                self.roles[role.id] = Role(role.id, label, self.roles[role.id].grant_delay)
        else:
            self.roles[role.id] = Role(role.id, label, role.grant_delay)

        return self.roles[role.id]

    def set_grant_delay(self, role: Role, delay: timedelta):
        if role.id in self.roles:
            if self.roles[role.id].grant_delay != delay:
                self.roles[role.id] = Role(role.id, self.roles[role.id].label, delay)
        else:
            self.roles[role.id] = Role(role.id, role.label, delay)

        return self.roles[role.id]

    def grant_role(self, role: Role, member: ChecksumAddress, execution_delay: timedelta = timedelta(0)):
        if role.id not in self.roles:
            self.roles[role.id] = role

        new_member = RoleMember(member, execution_delay)

        if new_member in self.role_members.get(role.id, set()):
            # Member already has the role, remove it in case the delay has changed
            self.role_members[role.id].remove(new_member)
        self.role_members[role.id].add(new_member)

        return new_member

    def revoke_role(self, role: Role, member: ChecksumAddress):
        if role.id not in self.roles:
            self.roles[role.id] = role

        member = RoleMember(member)
        if member in self.role_members.get(role.id, set()):
            self.role_members[role.id].remove(member)

    def set_role_admin(self, role: Role, admin: Role):
        if role.id not in self.roles:
            self.roles[role.id] = role
        if admin.id not in self.roles:
            self.roles[admin.id] = admin

        role = self.roles[role.id]
        admin = self.roles[admin.id]

        self.role_admins[role.id] = admin

    def set_role_guardian(self, role: Role, guardian: Role):
        if role.id not in self.roles:
            self.roles[role.id] = role
        if guardian.id not in self.roles:
            self.roles[guardian.id] = guardian

        role = self.roles[role.id]
        guardian = self.roles[guardian.id]

        self.role_guardians[role.id] = guardian

    def set_target_function_role(self, target: Target, selectors: Set[HexStr], role: Role):
        if role.id not in self.roles:
            self.roles[role.id] = role

        role = self.roles[role.id]

        if not selectors:
            return
        for selector in selectors:
            selector_role = SelectorRole(role, selector)
            if selector_role not in self.target_allowed_roles.get(target.address, set()):
                self.target_allowed_roles[target.address].add(selector_role)

    def set_target_closed(self, target: Target, closed: bool):
        if target.address not in self.targets:
            self.targets[target.address] = Target(target.address, closed, target.admin_delay)
        else:
            self.targets[target.address] = Target(
                target.address, closed, self.targets[target.address].admin_delay
            )

        return self.targets[target.address]

    def set_target_admin_delay(self, target: Target, delay: timedelta):
        if target.address not in self.targets:
            self.targets[target.address] = Target(target.address, target.closed, delay)
        else:
            self.targets[target.address] = Target(target.address, self.targets[target.address].closed, delay)

        return self.targets[target.address]

    def as_dict(self) -> dict:
        """Returns the current access manager state as a dict with only base types.

        The same dict can be used to create an AccessManager instance with the `from_dict` method.
        """
        return {
            "roles": {
                role.id: {
                    **role.as_dict(),
                    "guardian": self.get_role_guardian(role).as_dict(),
                    "admin": self.get_role_admin(role).as_dict(),
                    "members": [member.as_dict() for member in self.get_role_members(role)],
                    "targets": {
                        target.address: selectors
                        for target, selectors in self.get_all_role_targets(role).items()
                    },
                }
                for role in self.roles.values()
            },
            "targets": {address: target.as_dict for address, target in self.targets.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AccessManager":
        am = cls()
        for address, target_data in data.get("targets", {}).items():
            address = to_checksum_address(address)
            am.targets[address] = Target.from_dict(target_data)

        for role_id, role_data in data.get("roles", {}).items():
            role_id = int(role_id)
            am.label_role(Role(role_id), role_data["label"])
            am.set_grant_delay(Role(role_id), timedelta(seconds=role_data["grant_delay"]))
            am.set_role_admin(Role(role_id), Role(**role_data["admin"]))
            am.set_role_guardian(Role(role_id), Role(**role_data["guardian"]))
            for member_data in role_data["members"]:
                am.grant_role(
                    Role(role_id), member_data["address"], timedelta(seconds=member_data["execution_delay"])
                )

            for target_address, selectors in role_data["targets"].items():
                target = am.get_target(to_checksum_address(target_address))
                am.set_target_function_role(target, selectors, Role(role_id))
        return am


@dataclass
class Operation:
    # labelRole(uint64 roleId, string calldata label)
    # grantRole(uint64 roleId, address account, uint32 executionDelay)
    # revokeRole(uint64 roleId, address account)
    # setRoleAdmin(uint64 roleId, uint64 admin)
    # setRoleGuardian(uint64 roleId, uint64 guardian)
    # setGrantDelay(uint64 roleId, uint32 newDelay)
    # setTargetFunctionRole(address target, bytes4[] calldata selectors, uint64 roleId)
    # setTargetAdminDelay(address target, uint32 newDelay)
    op: Literal[
        "grantRole",
        "revokeRole",
        "setRoleGuardian",
        "setRoleAdmin",
        "labelRole",
        "setTargetFunctionRole",
        "setGrantDelay",
        "setTargetAdminDelay",
    ]
    args: dict

    def as_dict(self):
        return {"op": self.op, "args": self.args}
