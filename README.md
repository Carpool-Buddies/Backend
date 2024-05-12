## ✨ **Start the Flask API** via `Docker`

```bash
$ cd api-server-flask
$ docker-compose up --build  # Start with Docker
```

At this point, the API should be up & running at `http://localhost:5000`, and we can test the interface using POSTMAN or `curl`.

<br />

## ✨ General Information

The product is built using a `two-tier` pattern where the React frontend is decoupled logically and physically from the API backend. In order to use the product in a local environment, a few simple steps are required: 

- `Compile and start` the **Flask API Backend**
  - be default the server starts on port `5000`
- `Configuration` (Optional)
  - Change the API port
  - Configure the API port used by the React UI to communicate with the backend 

<br />

## ✨ Manual build

> 👉 **Start the Flask API** 

```bash
$ cd api-server-flask
$ 
$ # Create a virtual environment
$ virtualenv env
$ source env/bin/activate
$
$ # Install modules
$ pip install -r requirements.txt
$
$ # Set Up the Environment
$ export FLASK_APP=run.py
$ export FLASK_ENV=development
$ 
$ # Start the API
$ flask run 
```

<br />

### Configuration (Optional)

> Change the port exposed by the Flask API

```bash
$ flask run --port 5001
```

Now, the API can be accessed on port `5001`

<br />

> Update the API port used by the React Frontend

**API Server URL** - `src/config/constant.js` 

