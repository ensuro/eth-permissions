# Permissions visualization app

This project defines a simple app for obtaining and visualizing smart contract permissions in a graph.

It's aimed at contracts using [Openzeppelin's AccessControl module](https://docs.openzeppelin.com/contracts/3.x/api/access#AccessControl).

The backend is made in python and the frontend in react.

# Development

TODO: add docker-compose

Setup a virtualenv: `python3 -m venv venv; . venv/bin/activate; pip install -r requirements.txt`

## Run the backend

Requires a few environment variables. See [.env.sample](.env.sample).

```
cp .env.sample .env
# Fill out the variables in .env
flask run
```

The backend will also need the contract's ABI in order to obtain its events from the blockchain. For ensuro contracts you can install our npm package.

Example usage:

```
curl -s http://127.0.0.1:5000/api/graph/0x4181C295193bd7FBEbAcdA52352330de2327a6F5 > graph.dot
```


## Run the frontend

Nothing unusual:

```
cd frontend
npm start
```

# Deployment

TODO
