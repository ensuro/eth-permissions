# App for permissions auditing

In `main.py` you'll find an app developed for Google Cloud Functions.

It simply exposes the `build_graph` function on an http endpoint so that it can be used from a frontend.

There's a frontend for this app at https://ensuro.co/ens-permissions-frontend/

## Running the function locally

To run the function locally you will need a virtualenv with `functions-framework` and the app requirements:

```
python3 -m venv venv
. venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

It also requires a few environment variables. See [.env.sample](.env.sample).

```
cp .env.sample .env

# Review .env vars
$EDITOR .env

# Run the function
functions_framework --debug --target=permissions_graph
```

Then test it with:

```
curl -o test.gv http://127.0.0.1:8080/?address=0x47E2aFB074487682Db5Db6c7e41B43f913026544

dot -Tsvg test.gv > test.svg
```

# Deployment

Edit `config/environment.yml` with your config and then deploy with gcloud:

```
cd app
gcloud functions deploy permissions_graph \
    --env-vars-file environment.yml \
    --runtime python39 --trigger-http --allow-unauthenticated
```

Then test the deployed function with the URL that the gcloud CLI outputs:

```
URL=
curl "$URL"  | dot -Tsvg > test.svg
```
