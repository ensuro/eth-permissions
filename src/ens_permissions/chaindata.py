import itertools
import pathlib
from collections import defaultdict

from ethproto.wrappers import ETHWrapper, get_provider

from .roles import get_registry

CONTRACTS_PATH = pathlib.Path(__file__).parent / "contracts"


class EventStream:
    def __init__(self, contract_type, contract_address):
        self.contract_type = contract_type
        self.contract_address = contract_address
        self._event_stream = None

    def _load_stream(self):
        w3 = get_provider()

        if CONTRACTS_PATH not in w3.contracts_path:
            w3.contracts_path.append(CONTRACTS_PATH)

        contract_factory = w3.get_contract_factory(self.contract_type)
        contract = w3.build_contract(self.contract_address, contract_factory, self.contract_type)
        contract_wrapper = ETHWrapper.connect(contract)

        roles_granted = w3.get_events(contract_wrapper, "RoleGranted")
        roles_revoked = w3.get_events(contract_wrapper, "RoleRevoked")
        # TODO: admin_changes = w3.get_events(contract_wrapper, "RoleAdminChanged")

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
    def stream(self):
        if self._event_stream is None:
            self._load_stream()
        return self._event_stream

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
                    except KeyError:
                        raise RuntimeError(
                            f"WARNING: can't remove ungranted role {role} from {event['subject']}"
                        )
                else:
                    raise RuntimeError(f"Unexpected event {event.name} for role {role}")
        return [
            {"role": get_registry().get(role), "members": list(members)} for role, members in snapshot.items()
        ]
