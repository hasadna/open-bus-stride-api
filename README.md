# Open Bus Stride API

API For the Open Bus Stride project

## Development using the Docker Compose environment

This is the easiest option to start development, follow these instructions: https://github.com/hasadna/open-bus-pipelines/blob/main/README.md#stride-api

For local development, see the additional functionality section: `Develop stride-api from a local clone`

## Local Development

It's much easier to use the Docker Compose environment, but the following can be
refferd to for more details regarding the internal processes and for development
using your local Python interpreter. 

### Install

Create a virtualenv (using Python 3.8)

```
python3.8 -m venv venv
```

Update pip

```
venv/bin/pip install --upgrade pip
```

You should have a copy of open-bus-stride-db repository at ../open-bus-stride-db

Install dependencies

```
venv/bin/pip install -r requirements-dev.txt 
```

### Use

Start the stride-db from open-bus-pipelines docker-compose environment

Activate virtualenv

```
. venv/bin/activate
```

Start the FastAPI server with automatic reload on changes

```
uvicorn open_bus_stride_api.main:app --reload
```

See the API docs at http://localhost:8000/docs
