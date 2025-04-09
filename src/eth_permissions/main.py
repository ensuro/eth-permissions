import argparse
import json
from itertools import zip_longest

from environs import Env
from hexbytes import HexBytes

from eth_permissions import access_manager as am
from eth_permissions.access_control import Component, Role, get_registry
from eth_permissions.chaindata import AccessManagerEventStream
from eth_permissions.graph import build_graph
from eth_permissions.utils import safe_serializer

env = Env()
env.read_env()

KNOWN_ROLES = env.list("KNOWN_ROLES", ["GUARDIAN_ROLE", "LEVEL1_ROLE", "LEVEL2_ROLE", "LEVEL3_ROLE"])
KNOWN_COMPONENTS = env.list("KNOWN_COMPONENTS", [])
KNOWN_COMPONENT_NAMES = env.list("KNOWN_COMPONENT_NAMES", [])


parser = argparse.ArgumentParser(
    prog="eth-permissions", description="Command line tool for auditing smart contract permissions"
)
parser.add_argument(
    "-t",
    "--type",
    help="Contract type - AccessManager (default) or AccessControl",
    default="AccessManager",
    required=False,
    choices=["AccessManager", "AccessControl"],
)
parser.add_argument(
    "-c",
    "--compare-snapshot",
    help=(
        "Compare the current snapshot with the one in the given file. "
        "Prints out the differences in json format."
    ),
)
parser.add_argument("-o", "--output", help="Output file. Only valid for graph output")
parser.add_argument(
    "-f",
    "--format",
    required=False,
    default=None,
    help=(
        "Output format. Only valid for graph output. "
        "If ommitted it will be determined from the output file name extension"
    ),
)
parser.add_argument(
    "-v",
    "--view",
    action="store_true",
    required=False,
    help=(
        "If specified, the rendered file image will be opened with the default viewer. "
        "Only valid for graph output."
    ),
)
parser.add_argument("address", help="The contract's address")


def load_registry():
    get_registry().add_roles([Role(name) for name in KNOWN_ROLES])
    get_registry().add_components(
        [
            Component(HexBytes(address), name)
            for address, name in zip_longest(KNOWN_COMPONENTS, KNOWN_COMPONENT_NAMES)
        ]
    )


def main():
    args = parser.parse_args()

    if args.type == "AccessManager":
        event_stream = AccessManagerEventStream(args.address)
        # print(
        #     "\n".join(
        #         f"{e['event']} | " + " ".join(f"{k}={v}" for k, v in e["args"].items())
        #         for e in event_stream.stream
        #     )
        # )

        if args.compare_snapshot:
            with open(args.compare_snapshot, "r") as f:
                reference_snapshot = json.load(f)
            snapshot = am.AccessManager.from_dict(reference_snapshot)
            comparison = event_stream.compare(snapshot)
            print(json.dumps(comparison, indent=2, default=safe_serializer))
        else:
            snapshot = event_stream.snapshot_dict
            print(json.dumps(snapshot, indent=2, default=safe_serializer))
        return

    if not args.output:
        raise ValueError("Output file must be specified")

    load_registry()

    graph = build_graph(args.address)

    kwargs = {}
    if args.format:
        kwargs["format"] = args.format

    graph.render(outfile=args.output, cleanup=True, view=args.view, **kwargs)
