from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import airBox
from additional import fetch_and_save_additional_data
from constants import total_plot_name, total_plot_path, pm25_average_plot_name, pm25_average_plot_path

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(fetch_and_save_additional_data, 'interval', hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


class InputData(BaseModel):
    address: str


@app.post("/air-quality/query")
def query_air_quality(data: InputData):
    output = airBox.run(data)
    return output


@app.get("/plots/{plot_name}")
def get_plot(plot_name: str):

    if plot_name == total_plot_name:
        return FileResponse(total_plot_path)

    elif plot_name == pm25_average_plot_name:
        return FileResponse(pm25_average_plot_path)

    # for unknown plot
    raise HTTPException(status_code=404, detail="Plot not found")
