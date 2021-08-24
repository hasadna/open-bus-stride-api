# Open Bus Stride API

API For the Open Bus Stride project

## Local Development

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
