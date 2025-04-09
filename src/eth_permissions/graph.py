import graphviz

from .chaindata import AccessControlEventStream
from .utils import ExplorerAddress, ellipsize


def build_graph(contract_address):
    stream = AccessControlEventStream(contract_address)

    dot = graphviz.Digraph("Permissions")
    dot.attr(rankdir="RL", splines="ortho")
    dot.attr("node", style="rounded", shape="box")

    dot.node(
        "CONTRACT",
        URL=ExplorerAddress.get(contract_address),
        target="_blank",
        style="filled",
        fillcolor="green",
        shape="hexagon",
        fontcolor="blue",
    )

    for item in stream.snapshot:
        graphviz.quoting.quote(str(item["role"]))
        dot.node(item["role"].hash.hex(), str(item["role"]), tooltip=item["role"].hash.hex())
        # dot.edge(item["role"].hash.hex(), "CONTRACT")

        for member in item["members"]:
            dot.node(
                member,
                ellipsize(member),
                tooltip=member,
                URL=ExplorerAddress.get(member),
                target="_blank",
                style="filled",
                shape="hexagon",
                fontcolor="blue",
            )
            dot.edge(member, item["role"].hash.hex())

    return dot
