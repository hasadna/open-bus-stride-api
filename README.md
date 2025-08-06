# 🚌 Open Bus Stride API

**An API for the [Open Bus Stride Project](https://open-bus-map-search.hasadna.org.il/dashboard)**

## 📢 Get Involved

- 💬 For general help and system updates, join the Hasadna Slack: [#open-bus channel](https://join.slack.com/t/hasadna/shared_invite/zt-167h764cg-J18ZcY1odoitq978IyMMig)
- 🐞 Found a bug or have a feature request? [Open an issue](https://github.com/hasadna/open-bus-map-search/issues/new)
- 🤝 Want to contribute? See our [contributing guidelines](https://github.com/hasadna/open-bus-pipelines/blob/main/CONTRIBUTING.md)

## 🔗 Related Projects

### Frontend

- [🗺️ Open Bus Map Search (Client App)](https://github.com/hasadna/open-bus-map-search) - [Live Website](https://open-bus-map-search.hasadna.org.il/dashboard)
- [📦 Open Bus API Client (API Package Generator)](https://github.com/hasadna/open-bus-api-client) - [NPM Package](https://www.npmjs.com/package/@hasadna/open-bus-api-client)

### Backend

- [🏗️ Open Bus Pipelines](https://github.com/hasadna/open-bus-pipelines)
- [🌐 Open Bus Stride API (REST)](https://github.com/hasadna/open-bus-stride-api) – [API Docs](https://open-bus-stride-api.hasadna.org.il/docs)
- [🧾 Open Bus Stride DB](https://github.com/hasadna/open-bus-stride-db)
- [🔧 Open Bus Stride ETL](https://github.com/hasadna/stride-etl)
- [📚 Open Bus GTFS ETL](https://github.com/hasadna/gtfs-etl)
- [📡 Open Bus SIRI Requester](https://github.com/hasadna/siri-requester)
- [🧪 Open Bus SIRI ETL](https://github.com/hasadna/siri-etl)

## 🛠️ Tech Stack

- [Python](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/)

## 🚀 Getting Started

### Option 1: Using Docker Compose (Recommended)

The easiest way to get up and running is with Docker Compose.  
Follow the instructions [here](https://github.com/hasadna/open-bus-pipelines/blob/main/README.md#stride-api).

For local development (e.g. making changes to the code), also see:  
**`Develop stride-api from a local clone`** in the same document.

### Option 2: Local Development (Manual Setup)

Use this if you prefer to run directly from your local Python environment.

#### 1. Clone and Setup

Ensure you have **Python 3.8** installed.

```bash
python3.8 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements-dev.txt
```

Ensure a local clone of [open-bus-stride-db](https://github.com/hasadna/open-bus-stride-db) exists at:

```
../open-bus-stride-db
```

#### 2. Database Connection

You’ll need a database. You have two options:

- **Option A**: Start `stride-db` using the Docker Compose environment from [open-bus-pipelines](https://github.com/hasadna/open-bus-pipelines).
- **Option B**: Connect to the production DB using Redash read-only credentials.

Create a `.env` file:

```env
export SQLALCHEMY_URL=postgresql://postgres:123456@localhost
```

Then source it:

```bash
. .env
```

#### 3. Run the API Server

```bash
uvicorn open_bus_stride_api.main:app --reload
```

Access the interactive API docs at:
👉 [http://localhost:8000/docs](http://localhost:8000/docs)

## 🧩 API Development

All routes are defined in:

```
open_bus_stride_api/routers/<base_router_name>.py
```

### ✍️ Example API

```python
@router.<http_method>("/<api_path>", tags=["<tag_name>"], response_model=<ResponseModel>)
def name(<filtering_params>, limit, offset):
    return common.get_list(
        <DBModel>, limit, offset,
        [
            {'type': <filter_type>, 'field': <DBModel>.<field>, 'value': <filter_param>},
        ]
    )
```

- **Filters**: Defined in `routers/common.py` → `get_list_query_filter_<filter_type>`  (Examples: `'equal'`, `'date_in_range'`)

Always include `limit` and `offset` for pagination.

## 🧪 Running Tests

Set up your environment as described in the **Local Development** section above.

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

Ensure the DB contains full Stride data (production read-only access works).

Run tests:

```bash
pytest -svvx
```
