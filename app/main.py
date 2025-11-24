from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import airBox
from constants import total_plot_path, pm25_average_plot_path

class InputData(BaseModel):
    address: str


app = FastAPI()


@app.post("/run")
def run(data: InputData):
    output = airBox.run(data)
    return output

@app.get("/fig_one")
def get_total_plot():
    return FileResponse(total_plot_path)

@app.get("/fig_two")
def get_pm25_average():
    return FileResponse(pm25_average_plot_path)