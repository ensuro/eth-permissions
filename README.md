[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# Permissions audit package

This project defines a simple library for obtaining smart contract permissions and building a graph.

It's aimed at contracts using [Openzeppelin's AccessControl module](https://docs.openzeppelin.com/contracts/3.x/api/access#AccessControl).

There's a frontend for this at https://ensuro.co/ens-permissions-frontend/

# Development

There's an app developed for Google Cloud Functions.

To run the function locally you will need a virtualenv with `functions-framework` and the app requirements:

```
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt -r requirements.dev.txt
pip install -e .
```

## Running the function locally

Requires a few environment variables. See [.env.sample](.env.sample).

```
cp .env.sample .env

# Review .env vars
$EDITOR .env

# Run the function
functions_framework --debug --target=permissions_graph
```

Then test it with:

```
curl -o test.gv http://127.0.0.1:8080/?address=0xF7ED72430bEA07D8dB6eC264603811381F5af8e0

dot -Tsvg test.gv > test.svg
```

# Deployment

Edit `config/environment.yml` with your config and then deploy with gcloud:

```
gcloud functions deploy permissions_graph \
    --env-vars-file config/environment.yml \
    --runtime python39 --trigger-http --allow-unauthenticated
```

# TODO

- Deploy app from github actions
- Split `ens_permissions` into its own pypi library
- Add support for `Ownable` contracts
- Address book
- Add multisig intelligence (detect when a role member is a multisig and obtain its members)
- Timelock detection
