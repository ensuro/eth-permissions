import graphviz

from .chaindata import EventStream
from .utils import ExplorerAddress, ellipsize


def build_graph(contract_type, contract_address):
    stream = EventStream(contract_type, contract_address)

    dot = graphviz.Digraph("Permissions")
    dot.attr(rankdir="RL")
    dot.attr("node", style="rounded", shape="box")

    dot.node(
        "CONTRACT",
        URL=ExplorerAddress.get(contract_address),
        style="filled",
        fillcolor="green",
        shape="hexagon",
        fontcolor="blue",
    )

    for item in stream.snapshot:
        identifier = graphviz.quoting.quote(item["role"].name)
        dot.node(item["role"].hash, item["role"].name, tooltip=item["role"].hash)
        dot.edge(item["role"].hash, "CONTRACT")

        for member in item["members"]:
            dot.node(
                member,
                ellipsize(member),
                tooltip=member,
                URL=ExplorerAddress.get(member),
                style="filled",
                shape="hexagon",
                fontcolor="blue",
            )
            dot.edge(member, item["role"].hash)

    return dot
