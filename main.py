import functions_framework

from ens_permissions.graph import build_graph

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
}


@functions_framework.http
def permissions_graph(request):
    try:
        address = request.args["address"]
    except KeyError:
        return {"error": "address is required"}, 400

    graph = build_graph("IAccessControl", address)
    return (graph.source, 200, CORS_HEADERS)
