import importlib
import os
import traceback

from fastapi import FastAPI, Request
from sqlalchemy.exc import NoResultFound
from fastapi.responses import JSONResponse

from .version import VERSION
from .routers import ROUTER_NAMES

app = FastAPI(version=VERSION, title='Open Bus Stride API', description="""
### Follow planned and real-time bus statistics 🚌

Looking for a specific use-case?
* Take a look at the **user cases** APIs below.
* Try one of our existing notebooks-
  * [Load route rides to dataframe](https://mybinder.org/v2/gh/hasadna/open-bus-stride-client/HEAD?labpath=notebooks%2FLoad%20route%20rides%20to%20dataframe.ipynb)
  * [getting all arrivals to all stops of a given line on a given day](https://mybinder.org/v2/gh/hasadna/open-bus-stride-client/HEAD?labpath=notebooks%2Fgetting%20all%20arrivals%20to%20all%20stops%20of%20a%20given%20line%20in%20a%20given%20day.ipynb)
  * [load siri vehicle locations to pandas dataframe](https://mybinder.org/v2/gh/hasadna/open-bus-stride-client/main?labpath=notebooks%2Fload%20siri%20vehicle%20locations%20to%20pandas%20dataframe.ipynb)

* Don't see your use-case covered here? Please [open us a ticket](https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2Fhasadna%2Fopen-bus%2Fissues%2Fnew)!   


For more advanced usage-

* Use **gtfs** for data about the planned lines timetables. 
* Use **siri** for data about lines real-time
""")
print(os.getcwd())

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


@app.get("/", include_in_schema=False)
async def root():
    return {"ok": True}
