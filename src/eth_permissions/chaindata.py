import itertools
from collections import defaultdict
from datetime import timedelta
from warnings import warn

from ethproto.wrappers import ETHWrapper, get_provider

from . import abis
from . import access_manager as am
from .access_control import get_registry


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

    def _get_events(self, event_names):
        contract_wrapper = self._get_contract_wrapper()
        return self.provider.get_events(contract_wrapper, event_names)

    @property
    def stream(self):
        if self._event_stream is None:
            self._load_stream()
        return self._event_stream


class AccessControlEventStream(BaseEventStream):
    ABI = abis.OZ_ACCESS_CONTROL

    def _load_stream(self):
        events = self._get_events(["RoleGranted", "RoleRevoked"])  # TODO: RoleAdminChanged

        event_stream = []
        for event in events:
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
                        warn(f"WARNING: can't remove ungranted role {role} from {event['subject']}")
                else:
                    raise RuntimeError(f"Unexpected event {event.name} for role {role}")
        return [
            {"role": get_registry().get(role), "members": list(members)} for role, members in snapshot.items()
        ]


class AccessManagerEventStream(BaseEventStream):
    ABI = abis.OZ_ACCESS_MANAGER

    def _load_stream(self):
        events = self._get_events(
            [
                "RoleGranted",
                "RoleRevoked",
                "RoleGuardianChanged",
                "RoleAdminChanged",
                "RoleLabel",
                "TargetFunctionRoleUpdated",
                "RoleGrantDelayChanged",
                "TargetClosed",
                "TargetAdminDelayUpdated",
            ]
        )

        event_stream = [
            {
                "event": e.event,
                "args": e.args,
                "order": (e.blockNumber, e.logIndex),
            }
            for e in events
        ]

        self._event_stream = sorted(event_stream, key=lambda e: e["order"])

    @property
    def snapshot(self) -> am.AccessManager:
        """Returns a snapshot of the current permissions setup.

        The snapshot is an instance of AccessManager with the current state of the permissions.
        """
        return am.AccessManager.from_events(self.stream)

    @property
    def snapshot_dict(self) -> dict:
        return self.snapshot.as_dict()

    def compare(self, snapshot: am.AccessManager):
        """Compares the current snapshot with the given one. Returns the differences.

        snapshot must be a snapshot previously obtained from the snapshot property.

        The differences are returned as a series of operations to apply to bring the current state to the
        snapshot state.
        """
        current = self.snapshot
        differences = []

        for role_id, current_role in current.roles.items():
            snapshot_role = snapshot.roles.get(role_id, am.Role(id=role_id, label=""))

            if current_role.label != snapshot_role.label:
                differences.append(
                    am.Operation("labelRole", {"roleId": current_role, "label": snapshot_role.label})
                )
            if current.get_role_admin(current_role) != snapshot.get_role_admin(snapshot_role):
                differences.append(
                    am.Operation(
                        "setRoleAdmin",
                        {"roleId": current_role, "admin": snapshot.get_role_admin(snapshot_role)},
                    )
                )
            if current.get_role_guardian(current_role) != snapshot.get_role_guardian(snapshot_role):
                differences.append(
                    am.Operation(
                        "setRoleGuardian",
                        {"roleId": current_role, "guardian": snapshot.get_role_guardian(snapshot_role)},
                    )
                )
            if current_role.grant_delay != snapshot_role.grant_delay:
                differences.append(
                    am.Operation(
                        "setGrantDelay",
                        {"roleId": current_role, "newDelay": snapshot_role.grant_delay},
                    )
                )

            if current.get_role_members(current_role) != snapshot.get_role_members(snapshot_role):
                for member in current.get_role_members(current_role) - snapshot.get_role_members(
                    snapshot_role
                ):
                    differences.append(
                        am.Operation("revokeRole", {"roleId": current_role, "account": member.address})
                    )

                for member in snapshot.get_role_members(snapshot_role) - current.get_role_members(
                    current_role
                ):
                    differences.append(
                        am.Operation(
                            "grantRole",
                            {
                                "roleId": current_role,
                                "account": member.address,
                                "executionDelay": member.execution_delay,
                            },
                        )
                    )

            # For common members just need to check the execution delay is properly set
            for common_member in current.get_role_members(current_role) & snapshot.get_role_members(
                snapshot_role
            ):
                # Can't get te members from iterating the intersection, because we need to distinguish them
                current_member = [
                    member for member in current.get_role_members(current_role) if member == common_member
                ][0]
                snapshot_member = [
                    member for member in snapshot.get_role_members(snapshot_role) if member == common_member
                ][0]
                if current_member.execution_delay != snapshot_member.execution_delay:
                    differences.append(
                        am.Operation(
                            "grantRole",
                            {
                                "roleId": current_role,
                                "account": snapshot_member.address,
                                "executionDelay": snapshot_member.execution_delay,
                            },
                        )
                    )

        snapshot_targets = set(snapshot.targets.values())
        current_targets = set(current.targets.values())
        if current_targets != snapshot_targets:
            # The targets not present in the snapshot need to be reset to default values
            for target in current_targets - snapshot_targets:
                if target.closed:
                    differences.append(am.Operation("setTargetClosed", {"target": target, "closed": False}))
                if target.admin_delay != timedelta(0):
                    differences.append(am.Operation("setTargetAdminDelay", {"target": target, "newDelay": 0}))

            # The targets in snapshot but missing from current need to be properly configured
            for target in snapshot_targets - current_targets:
                if target.closed:
                    differences.append(
                        am.Operation("setTargetClosed", {"target": target, "closed": target.closed})
                    )
                if target.admin_delay != timedelta(0):
                    differences.append(
                        am.Operation(
                            "setTargetAdminDelay", {"target": target, "newDelay": target.admin_delay}
                        )
                    )

            # The common targets need to be checked for matching config
            for common_target in current_targets & snapshot_targets:
                current_target = [target for target in current_targets if target == common_target][0]
                snapshot_target = [target for target in snapshot_targets if target == common_target][0]
                if current_target.closed != snapshot_target.closed:
                    differences.append(
                        am.Operation(
                            "setTargetClosed", {"target": current_target, "closed": snapshot_target.closed}
                        )
                    )
                if current_target.admin_delay != snapshot_target.admin_delay:
                    differences.append(
                        am.Operation(
                            "setTargetAdminDelay",
                            {"target": current_target, "newDelay": snapshot_target.admin_delay},
                        )
                    )

        current_selectors = {
            (target, selector_role.selector)
            for target, selector_roles in current.target_allowed_roles.items()
            for selector_role in selector_roles
        }
        snapshot_selectors = {
            (target, selector_role.selector)
            for target, selector_roles in snapshot.target_allowed_roles.items()
            for selector_role in selector_roles
        }

        if current_selectors != snapshot_selectors:
            # The target -> selectors not present in the snapshot need to be assigned to ADMIN_ROLE
            for target, selector in current_selectors - snapshot_selectors:
                differences.append(
                    am.Operation(
                        "setTargetFunctionRole",
                        {
                            "target": target,
                            "selectors": {selector},
                            "roleId": snapshot.ADMIN_ROLE,
                        },
                    )
                )

            # The target -> selectors in snapshot missing from current need to be set on current
            for target, selector in snapshot_selectors - current_selectors:
                role = snapshot.get_target_allowed_role(target, selector)
                if role == snapshot.ADMIN_ROLE:
                    continue
                differences.append(
                    am.Operation(
                        "setTargetFunctionRole",
                        {
                            "target": target,
                            "selectors": {selector},
                            "roleId": role,
                        },
                    )
                )

        # The common target -> selectors need to be checked for matching role
        for common_target, common_selector in current_selectors & snapshot_selectors:
            current_role = current.get_target_allowed_role(common_target, common_selector)
            snapshot_role = snapshot.get_target_allowed_role(common_target, common_selector)
            if current_role != snapshot_role:
                differences.append(
                    am.Operation(
                        "setTargetFunctionRole",
                        {
                            "target": common_target,
                            "selectors": {common_selector},
                            "roleId": snapshot_role,
                        },
                    )
                )

        return differences
