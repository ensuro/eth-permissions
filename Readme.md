# Permissions visualization app

This project defines a simple app for obtaining and visualizing smart contract permissions in a graph.

It's aimed at contracts using [Openzeppelin's AccessControl module](https://docs.openzeppelin.com/contracts/3.x/api/access#AccessControl).

The backend is made in python and the frontend in react.

# Running the backend

Requires a few environment variables. See [.env.sample](.env.sample).

```
cp .env.sample .env
# Fill out the variables in .env
flask run
```

# Running the frontend

Nothing unusual:

```
cd frontend
npm start
```
