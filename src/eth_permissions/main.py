import argparse
from itertools import zip_longest

from environs import Env
from hexbytes import HexBytes

from eth_permissions.graph import build_graph
from eth_permissions.roles import Component, Role, get_registry

env = Env()
KNOWN_ROLES = env.list("KNOWN_ROLES", ["GUARDIAN_ROLE", "LEVEL1_ROLE", "LEVEL2_ROLE", "LEVEL3_ROLE"])
KNOWN_COMPONENTS = env.list("KNOWN_COMPONENTS", [])
KNOWN_COMPONENT_NAMES = env.list("KNOWN_COMPONENT_NAMES", [])


parser = argparse.ArgumentParser(
    prog="eth-permissions", description="Command line tool for auditing smart contract permissions"
)
parser.add_argument("-o", "--output", required=True, help="Output file")
parser.add_argument(
    "-f",
    "--format",
    required=False,
    default=None,
    help="Output format. If ommitted it will be determined from the output file name extension",
)
parser.add_argument(
    "-v",
    "--view",
    action="store_true",
    required=False,
    help="If specified, the rendered file image will be opened with the default viewer.",
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
    load_registry()

    graph = build_graph("IAccessControl", args.address)

    kwargs = {}
    if args.format:
        kwargs["format"] = args.format

    graph.render(outfile=args.output, cleanup=True, view=args.view, **kwargs)
