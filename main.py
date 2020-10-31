from fastapi import FastAPI # noqa
import json

app = FastAPI()

@app.get("/")
async def read_root():
    with open('data.json') as json_file:
        data = json.load(json_file)
    return {"message": data}
