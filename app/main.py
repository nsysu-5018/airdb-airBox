from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import airBox
from constants import total_plot_name, total_plot_path, pm25_average_plot_name, pm25_average_plot_path

class InputData(BaseModel):
    address: str


app = FastAPI()


@app.post("/air-quality/query")
def query_air_quality(data: InputData):
    output = airBox.run(data)
    return output

@app.get("/plots/{plot_name}")
def get_plot(plot_name:str):

    if plot_name == total_plot_name:
        return FileResponse(total_plot_path)

    elif plot_name == pm25_average_plot_name:
        return FileResponse(pm25_average_plot_path)

    # for unknown plot
    raise HTTPException(status_code=404, detail="Plot not found")
