[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# Eth permissions audit library

This project defines a simple library for obtaining smart contract permissions and building a graph.

It's aimed at contracts using [Openzeppelin's AccessControl module](https://docs.openzeppelin.com/contracts/3.x/api/access#AccessControl).

# Installation

Simply install with `pip` or your preferred package manager:

```
pip install eth-permissions
```

# Usage

We use [eth-prototype](https://pypi.org/project/eth-prototype/)'s wrappers for accessing the blockchain information. The simplest way to use it is to export the following environment variables:

```sh
export DEFAULT_PROVIDER=w3

# You can use any json-rpc node supported by web3py.
export WEB3_PROVIDER_URI=https://polygon-mainnet.g.alchemy.com/v2/<YOUR KEY>
```

With that set, getting the permissions graph is very simple:

```python
from eth_permissions.roles import get_registry, Role
from eth_permissions.graph import build_graph

# Optionally register any known roles
known_roles = ["GUARDIAN_ROLE", "LEVEL1_ROLE", "LEVEL2_ROLE", "LEVEL3_ROLE"]
roles_registry = get_registry()
roles_registry.add_roles([Role(name) for name in known_roles])

# Build the graph
contract_address = "0x47E2aFB074487682Db5Db6c7e41B43f913026544"

g = build_graph("IAccessControl", contract_address)
g.render("my_permissions.gv", format="svg")
```

This will save the graphviz file in `my_permissions.gv` and render it in `my_permissions.gv.svg`. The svg format was chosen for this example because it supports tooltips.

## Getting the permissions snapshot for programmatic use

In some cases you may want just the permissions in a consistent datastructure to use from your code.

Export the eth node environment variables as above and use the `chaindata` module to get the full permissions detail:

```python
from eth_permissions.chaindata import EventStream

stream = EventStream("IAccessControl", "0x47E2aFB074487682Db5Db6c7e41B43f913026544")

stream.snapshot

# [
#  {'role': Role('DEFAULT_ADMIN_ROLE'),
#   'members': ['0xCfcd29CD20B6c64A4C0EB56e29E5ce3CD69336D2']},
#  {'role': Role('UNKNOWN ROLE: 0x2582...a559'),
#   'members': ['0x9dA2192C820C5cC37d26A3F97d7BcF1Bc04232A3']},
#  ...
#  {'role': Role('UNKNOWN ROLE: 0xf17c...fd8a'),
#   'members': ['0x76B349e14a5B5FAF8090313Aa393e1b37aC5E126']},
# ]
```

As well as in the previous example, you can register your roles to get the actual names in the result.

# App

Check [docs/App](docs/App.md) for a simple app that exposes this API over http for use on a frontend app.

# TODO

- Add support for `Ownable` contracts
- Address book
- Add multisig intelligence (detect when a role member is a multisig and obtain its members)
- Timelock detection
