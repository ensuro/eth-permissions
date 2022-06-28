# Permissions audit app

This project defines a simple app for obtaining smart contract permissions and building a graph.

It's aimed at contracts using [Openzeppelin's AccessControl module](https://docs.openzeppelin.com/contracts/3.x/api/access#AccessControl).

There's a frontend for this app at TODO

# Development

This app is developed for Google Cloud Functions.

To run the function locally you will need a virtualenv with `functions-framework` and the app requirements:

```
python3 -m venv venv
. venv/bin/activate
pip install functions-framework
pip install -r requirements.txt
```

## Running the function locally

Requires a few environment variables. See [.env.sample](.env.sample).

```
cp .env.sample .env

# Review .env vars and export them:
set -a; source .env; set +a

# Run the function
functions_framework --debug --target=permissions_graph
```

# Deployment

Edit `config/environment.yml` with your config and then deploy with gcloud:

```
gcloud functions deploy permissions_graph \
    --env-vars-file config/environment.yml \
    --runtime python39 --trigger-http --allow-unauthenticated
```




# TODO

- Deploy from github actions
- Split `ens_permissions` into its own pypi library
- Add support for `Ownable` contracts
- Address book
- Add multisig intelligence (detect when a role member is a multisig and obtain its members)
- Timelock detection