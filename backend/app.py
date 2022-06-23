from flask import Flask
from flask_cors import CORS

from ens_permissions.graph import build_graph

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/api/graph/<address>")
def get_graph(address):
    graph = build_graph("PolicyPoolConfig", address)
    return graph.source
