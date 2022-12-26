[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# Eth permissions audit library

This project defines a simple library for obtaining smart contract permissions and building a graph.

It's aimed at contracts using [Openzeppelin's AccessControl module](https://docs.openzeppelin.com/contracts/3.x/api/access#AccessControl).

# Installation

Simply install with `pip` or your preferred package manager:

```
pip install eth-permissions
```

# Usage as a library

We use [eth-prototype](https://pypi.org/project/eth-prototype/)'s wrappers for accessing the blockchain information. The simplest way to use it is to export the following environment variables:

```sh
export DEFAULT_PROVIDER=w3

# You can use any json-rpc node supported by web3py.
export WEB3_PROVIDER_URI=https://polygon-mainnet.g.alchemy.com/v2/<YOUR KEY>
```

Use the `chaindata` module to get the full permissions detail:

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

You can register your roles to get the actual names in the result. See [main.py](src/eth_permissions/main.py) for an example of how to do that.

# Usage as a command line tool

First set up some env vars:

```
# Env vars for eth-prototype
export DEFAULT_PROVIDER=w3
export WEB3_PROVIDER_URI=https://polygon-mainnet.g.alchemy.com/v2/<YOUR KEY>

# Values for ensuro v2 on mainnet as of dec 2023, change accordingly for other contracts
export KNOWN_ROLES=GUARDIAN_ROLE,LEVEL1_ROLE,LEVEL2_ROLE,LEVEL3_ROLE,RESOLVER_ROLE,POLICY_CREATOR_ROLE,PRICER_ROLE,...
export KNOWN_COMPONENTS=0xa65c9dE776d1f30c095EFF9C775E001a1d366df8,0x37fE456EFF897CB5dDF040A5e95f399EaBc162ca
export KNOWN_COMPONENT_NAMES="KoalaV2,Koala Partner B"
```

Then run `eth-permissions`:

```
python -m eth_permissions --view --output test.png 0x47E2aFB074487682Db5Db6c7e41B43f913026544
```

This will create the file `test.png` and open it with the default viewer. It will look like this:

![](images/ensuro_mainnet_graph.png)

Run `python -m eth_permissions --help` to see all available flags and options.

# App

Check [app/Readme](app/README.md) for a simple app that exposes this API over http for use on a frontend app.

# TODO

- Add support for `Ownable` contracts
- Address book
- Add multisig intelligence (detect when a role member is a multisig and obtain its members)
- Timelock detection
