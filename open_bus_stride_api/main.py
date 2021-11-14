from fastapi import FastAPI, Request
from sqlalchemy.exc import NoResultFound
from fastapi.responses import JSONResponse

from .routers import siri_vehicle_locations
from .routers import siri_snapshots
from .routers import rides
from .routers import routes
from .routers import route_stops
from .routers import stops
from .version import VERSION


app = FastAPI(version=VERSION, title='Open Bus Stride API')


@app.exception_handler(NoResultFound)
def sqlalchemy_no_result_found_exception_handler(request: Request, exc: NoResultFound):
    return JSONResponse(status_code=404, content={"message": str(exc)})


app.include_router(siri_vehicle_locations.router, prefix='/siri_vehicle_locations')
app.include_router(siri_snapshots.router, prefix='/siri_snapshots')
app.include_router(rides.router, prefix='/rides')
app.include_router(routes.router, prefix='/routes')
app.include_router(route_stops.router, prefix='/route_stops')
app.include_router(stops.router, prefix='/stops')


@app.get("/")
async def root():
    return {"ok": True}
