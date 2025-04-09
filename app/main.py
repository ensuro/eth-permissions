from itertools import zip_longest

import functions_framework
from environs import Env
from hexbytes import HexBytes

from eth_permissions.access_control import Component, Role, get_registry
from eth_permissions.graph import build_graph

env = Env()
env.read_env()

KNOWN_ROLES = env.list("KNOWN_ROLES", ["GUARDIAN_ROLE", "LEVEL1_ROLE", "LEVEL2_ROLE", "LEVEL3_ROLE"])
KNOWN_COMPONENTS = env.list("KNOWN_COMPONENTS", [])
KNOWN_COMPONENT_NAMES = env.list("KNOWN_COMPONENT_NAMES", [])  # TODO: we should get the names from chain

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
}

if len(KNOWN_COMPONENTS) < len(KNOWN_COMPONENT_NAMES):
    raise RuntimeError("Can't have a component name without address")

get_registry().add_roles([Role(name) for name in KNOWN_ROLES])
get_registry().add_components(
    [
        Component(HexBytes(address), name)
        for address, name in zip_longest(KNOWN_COMPONENTS, KNOWN_COMPONENT_NAMES)
    ]
)


@functions_framework.http
def permissions_graph(request):
    try:
        address = request.args["address"]
    except KeyError:
        return {"error": "address is required"}, 400

    graph = build_graph(address)
    return (graph.source, 200, CORS_HEADERS)
