# Open Bus Stride API

API For the [Open Bus Stride project](https://open-bus-map-search.hasadna.org.il/dashboard)

* Please report issues and feature requests [here](https://github.com/hasadna/open-bus/issues/new)
* To get updates about the system status and for general help join Hasadna's Slack #open-bus channel ([Hasadna Slack signup link](https://join.slack.com/t/hasadna/shared_invite/zt-167h764cg-J18ZcY1odoitq978IyMMig))

See [our contributing docs](https://github.com/hasadna/open-bus-pipelines/blob/main/CONTRIBUTING.md) if you want to suggest changes to this repository.


## Tech Stack

- [python](https://www.python.org/)
- [fastAPI framework](https://fastapi.tiangolo.com/)
- [postgresql](https://www.postgresql.org/)


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

You need a DB to connect to, there are 2 options here:

* Start the stride-db from open-bus-pipelines docker-compose environment
* Connect to the production DB using the Redash read-only credentials
  * Create a `.env` file with the following, replacing the url to the production redash read-only url: `export SQLALCHEMY_URL=postgresql://postgres:123456@localhost`
  * Source the .env: `. .env`

Activate virtualenv

```
. venv/bin/activate
```

Start the FastAPI server with automatic reload on changes

```
uvicorn open_bus_stride_api.main:app --reload
```

See the API docs at http://localhost:8000/docs

### Manage APIs

All existing APIs from the docs are defined under ```open_bus_stride_api/routers/<base_router_name>.py```

Follow this example to create or edit a simple API for a specific table with filters: 


```
@router.<http_method>("/<api_path>", tags=[<file_name>], response_model=<pydantic_response_model>) // 
def name(<filtering_params>, limit, offset): # always include limit & offest to allow easy iteration on the data
    return common.get_list(
        <db_model>, limit, offset,
        [   
            {'type': <filter_type>, 'field': <db_stcruct>.<specific_id>, 'value': <filter_param>},
        ]
    )
```

Filter types are defined at ```open_bus_stride_api/routers/common.py -> get_list_query_filter_<filter_type>``` (e.g.: 'equal', 'date_in_range')

### Running Tests

Install for local development as described above.

Install test requirements:

```
pip install -r tests/requirements.txt
```

To run the tests you need to connect to a DB with full stride data, 
easiest way is to connect to the production DB as described above by
setting the SQLALCHEMY_URL env var accordingly.

Run all tests with full output, exiting on first error:

```
pytest -svvx
```

Pytest has many options, see the help message for details.


### Link To The Client Repo
- [client repo](https://github.com/hasadna/open-bus-map-search)