
import base64
import io

from fastapi import FastAPI, Request, HTTPException, Form, UploadFile
import uvicorn
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import logging
import docker
import requests
import json
import hashlib
import datetime
from queries.Users import queries as userQueries
from queries.DigitalModels import queries as dmQueries
from queries.MongoJSONEncoder import MongoJSONEncoder
import pandas as pd

app = FastAPI(middleware=[
    Middleware(CORSMiddleware, allow_origins=["*"])
])
dockerClient = docker.from_env()

image_digital_model_name = "jesuscumpli/model-digital"
image_digital_model_tag = "mdv5"
image_real_sytem_name = "jesuscumpli/model-digital"
image_real_system_tag = "mdv5"
container_id_real_system = "a366d74f-dc6e-4132-8df8-8e7d6c9f0b07"
container_real_system_name = "real-system"

@app.post("/replace_actual_model2")
async def replace_actual_model():
    print("SUCCESSSSSS")
    # print(type(model_bytes))
    # print(type(evaluation_dict))
    print("SUCCESSSSSS")
    return {"success": True}

@app.post("/replace_actual_model")
async def replace_actual_model(model_bytes: bytes):
    print("SUCCESSSSSS")
    print(type(model_bytes))
    # print(type(evaluation_dict))
    print("SUCCESSSSSS")
    return {"success": True}



if __name__ == "__main__":
    try:
        ip = "0.0.0.0"
        port = "8081"
        uvicorn.run(app, host=ip, port=int(port))
    except Exception as e:
        logging.exception("Error en API: " + str(e))
