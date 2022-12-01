import itertools
import pathlib
from collections import defaultdict

from environs import Env
from ethproto.wrappers import ETHWrapper, get_provider
from web3 import Web3

from .utils import ellipsize

env = Env()

KNOWN_ROLES = env.list(
    "KNOWN_ROLES",
    default=["GUARDIAN_ROLE", "LEVEL1_ROLE", "LEVEL2_ROLE", "LEVEL3_ROLE"],
)

# Roles rainbow table
DEFAULT_ADMIN_ROLE_HASH = "0x" + "0" * 64
ROLES_TABLE = {Web3.keccak(text=role).hex(): role for role in KNOWN_ROLES}
ROLES_TABLE[DEFAULT_ADMIN_ROLE_HASH] = "DEFAULT_ADMIN_ROLE"

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
        contract = w3.build_contract(
            self.contract_address, contract_factory, self.contract_type
        )
        contract_wrapper = ETHWrapper.connect(contract)

        roles_granted = w3.get_events(contract_wrapper, "RoleGranted")
        roles_revoked = w3.get_events(contract_wrapper, "RoleRevoked")
        # TODO: admin_changes = w3.get_events(contract_wrapper, "RoleAdminChanged")

        event_stream = []
        for event in roles_granted + roles_revoked:
            event_stream.append(
                {
                    "role": Role("0x" + event.args.role.hex()),
                    "subject": event.args.account,
                    "requester": event.args.sender,
                    "order": (event.blockNumber, event.logIndex),
                    "event": event.event,
                }
            )
        self._event_stream = sorted(
            event_stream, key=lambda e: (e["role"].hash, e["order"])
        )

    @property
    def stream(self):
        if self._event_stream is None:
            self._load_stream()
        return self._event_stream

    @property
    def snapshot(self):
        snapshot = defaultdict(set)
        for role, events in itertools.groupby(
            self.stream, key=lambda e: e["role"].hash
        ):
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
            {"role": Role(role), "members": list(members)}
            for role, members in snapshot.items()
        ]


class Role:
    def __init__(self, hash):
        self.hash = hash
        self.name = ROLES_TABLE.get(self.hash, f"UNKNOWN ROLE: {ellipsize(hash)}")

    def __str__(self):
        return f"Role:{self.name}"

    def __repr__(self):
        return f"Role('{self.hash}')"
