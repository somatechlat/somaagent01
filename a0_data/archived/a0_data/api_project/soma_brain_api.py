import fastapi
from fastapi import FastAPI
app = FastAPI()
@app.get("/soma_brain")
def read_soma_brain():
    return {"message": "SomaBrain API endpoint"}