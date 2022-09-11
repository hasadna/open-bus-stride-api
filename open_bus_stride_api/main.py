import importlib
import os
import traceback

from fastapi import FastAPI, Request
from sqlalchemy.exc import NoResultFound
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from .version import VERSION
from .routers import ROUTER_NAMES


with open(os.path.join(os.path.dirname(__file__), "DESCRIPTION.md"), "r") as f:
    description = f.read()

app = FastAPI(version=VERSION, title='Open Bus Stride API', description=description)

@app.exception_handler(NoResultFound)
def sqlalchemy_no_result_found_exception_handler(request: Request, exc: NoResultFound):
    return JSONResponse(status_code=404, content={"message": str(exc)})


@app.exception_handler(Exception)
def generic_error_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"message": str(exc), "traceback": traceback.format_tb(exc.__traceback__)})


for router_name in ROUTER_NAMES:
    app.include_router(
            importlib.import_module('open_bus_stride_api.routers.{}'.format(router_name)).router,
        prefix='/{}'.format(router_name)
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins='*',
)

@app.get("/", include_in_schema=False)
async def root():
    return {"ok": True}
