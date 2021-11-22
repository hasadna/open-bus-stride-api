import importlib

from fastapi import FastAPI, Request
from sqlalchemy.exc import NoResultFound
from fastapi.responses import JSONResponse

from .version import VERSION
from .routers import ROUTER_NAMES


app = FastAPI(version=VERSION, title='Open Bus Stride API')


@app.exception_handler(NoResultFound)
def sqlalchemy_no_result_found_exception_handler(request: Request, exc: NoResultFound):
    return JSONResponse(status_code=404, content={"message": str(exc)})


for router_name in ROUTER_NAMES:
    app.include_router(
        importlib.import_module('open_bus_stride_api.routers.{}'.format(router_name)).router,
        prefix='/{}'.format(router_name)
    )


@app.get("/", include_in_schema=False)
async def root():
    return {"ok": True}
