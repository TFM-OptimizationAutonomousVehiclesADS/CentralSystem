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


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/digital-models/all")
async def all_digital_models():
    containers = dockerClient.containers.list(all=True, filters={
        "ancestor": f"{image_digital_model_name}:{image_digital_model_tag}"})
    digital_models = []
    for container in containers:
        if container_real_system_name in container.attrs["Name"]:
            continue
        data = {}
        data["id"] = container.id
        data["status"] = container.attrs["State"]["Status"]
        data["state"] = container.attrs["State"]
        data["short_id"] = container.short_id
        data["name"] = container.attrs["Name"]
        data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
        data["image"] = container.attrs["Config"]["Image"]
        data["params"] = container.attrs["Config"]["Env"]
        data["created"] = container.attrs["Created"]
        try:
            dataQueriesMongo = dmQueries.findDigitalModelByIdMongo(container.id)
            data["mongo"] = dataQueriesMongo
        except Exception as e:
            print(e)
        digital_models.append(data)
    return {"digital_models": digital_models, "docker": True}


@app.post("/digital-models/new")
async def digital_models_new(info: Request):
    info_json = await info.form()

    container_name = info_json["container_name"]
    # dockerClient.images.pull(repository=image_digital_model_name, tag=image_digital_model_tag)
    options = {
        "image": f"{image_digital_model_name}:{image_digital_model_tag}",
        "name": container_name,
        "detach": True,  # Ejecutar el contenedor en segundo plano
        "ports": {"8001/tcp": None},
        "environment": {
            "DIGITAL_MODEL_NAME": container_name,
            "DIGITAL_MODEL_USERNAME_OWNER": info_json["DIGITAL_MODEL_USERNAME_OWNER"],
            "DIGITAL_MODEL_RETRAINING_TEST_SIZE": float(info_json["DIGITAL_MODEL_RETRAINING_TEST_SIZE"]),
            "DIGITAL_MODEL_RETRAINING_TUNNING": int(info_json["DIGITAL_MODEL_RETRAINING_TUNNING"] == "true"),
            "DIGITAL_MODEL_RETRAINING_MIN_SPLIT": int(info_json["DIGITAL_MODEL_RETRAINING_MIN_SPLIT"]),
            "DIGITAL_MODEL_RETRAINING_MAX_SPLIT": int(info_json["DIGITAL_MODEL_RETRAINING_MAX_SPLIT"]),
            "DIGITAL_MODEL_RETRAINING_MIN_EPOCHS": int(info_json["DIGITAL_MODEL_RETRAINING_MIN_EPOCHS"]),
            "DIGITAL_MODEL_RETRAINING_MAX_EPOCHS": int(info_json["DIGITAL_MODEL_RETRAINING_MAX_EPOCHS"]),
            "DIGITAL_MODEL_RETRAINING_BEST_EPOCH": int(info_json["DIGITAL_MODEL_RETRAINING_BEST_EPOCH"] == "true"),
            "DIGITAL_MODEL_RETRAINING_RETRAIN_WEIGHTS": int(
                info_json["DIGITAL_MODEL_RETRAINING_RETRAIN_WEIGHTS"] == "true"),
            "DIGITAL_MODEL_RETRAINING_RANDOM_SAMPLES": int(
                info_json["DIGITAL_MODEL_RETRAINING_RANDOM_SAMPLES"] == "true"),
            "DIGITAL_MODEL_SIZE_IMAGES_WIDTH": int(info_json["DIGITAL_MODEL_SIZE_IMAGES_WIDTH"]),
            "DIGITAL_MODEL_SIZE_IMAGES_HEIGHT": int(info_json["DIGITAL_MODEL_SIZE_IMAGES_HEIGHT"]),
            "DIGITAL_MODEL_THRESHOLD_ANOMALY": float(info_json["DIGITAL_MODEL_THRESHOLD_ANOMALY"]),
            "DIGITAL_MODEL_SIZE_IMAGES_OPTIMIZER": "adam",
            "DIGITAL_MODEL_SIZE_IMAGES_LOSS": "binary_crossentropy",
            "DIGITAL_MODEL_SIZE_IMAGES_METRICS": json.dumps(['accuracy', 'f1_score', 'recall', 'precision']),
            "DIGITAL_MODEL_SIZE_IMAGES_METRIC_OBJECTIVE": info_json["DIGITAL_MODEL_SIZE_IMAGES_METRIC_OBJECTIVE"],
            "DIGITAL_MODEL_SIZE_IMAGES_FLOAT_FEATURES": json.dumps(['channel_camera', 'speed', 'rotation_rate_z']),
            "DIGITAL_MODEL_SIZE_IMAGES_IMAGES_FEATURES": json.dumps(
                ['filename_resized_image', 'filename_objects_image', 'filename_surfaces_image']),
        }
    }
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.run(**options)
    container_data = {}
    if container:
        data = {}
        data["id"] = container.id
        data["status"] = container.attrs["State"]["Status"]
        data["short_id"] = container.short_id
        data["name"] = container.attrs["Name"]
        data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
        data["image"] = container.attrs["Config"]["Image"]
        data["params"] = container.attrs["Config"]["Env"]
        container_data = data
        return {"container": container_data}


@app.post("/real-system/start")
async def real_system_new():
    try:
        container = dockerClient.containers.get(container_real_system_name)
    except Exception as e:
        container = None
    if container:
        container.start()
    else:
        options = {
            "image": f"{image_real_sytem_name}:{image_real_system_tag}",
            "name": container_real_system_name,
            "detach": True,  # Ejecutar el contenedor en segundo plano
            "ports": {"8001/tcp": None},
            "environment": {
                "IS_REAL_SYSTEM": int(1),
                "DIGITAL_MODEL_NAME": container_real_system_name,
                "DIGITAL_MODEL_USERNAME_OWNER": 'admin',
                "DIGITAL_MODEL_RETRAINING_TEST_SIZE": float(0.25),
                "DIGITAL_MODEL_RETRAINING_TUNNING": int(0),
                "DIGITAL_MODEL_RETRAINING_MIN_SPLIT": int(2000),
                "DIGITAL_MODEL_RETRAINING_MAX_SPLIT": int(2000),
                "DIGITAL_MODEL_RETRAINING_MIN_EPOCHS": int(10),
                "DIGITAL_MODEL_RETRAINING_MAX_EPOCHS": int(100),
                "DIGITAL_MODEL_RETRAINING_BEST_EPOCH": int(0),
                "DIGITAL_MODEL_RETRAINING_RETRAIN_WEIGHTS": int(1),
                "DIGITAL_MODEL_RETRAINING_RANDOM_SAMPLES": int(1),
                "DIGITAL_MODEL_SIZE_IMAGES_WIDTH": int(80),
                "DIGITAL_MODEL_SIZE_IMAGES_HEIGHT": int(45),
                "DIGITAL_MODEL_THRESHOLD_ANOMALY": float(0.5),
                "DIGITAL_MODEL_SIZE_IMAGES_OPTIMIZER": "adam",
                "DIGITAL_MODEL_SIZE_IMAGES_LOSS": "binary_crossentropy",
                "DIGITAL_MODEL_SIZE_IMAGES_METRICS": json.dumps(['accuracy', 'f1_score', 'recall', 'precision']),
                "DIGITAL_MODEL_SIZE_IMAGES_METRIC_OBJECTIVE": 'f1_score',
                "DIGITAL_MODEL_SIZE_IMAGES_FLOAT_FEATURES": json.dumps(['channel_camera', 'speed', 'rotation_rate_z']),
                "DIGITAL_MODEL_SIZE_IMAGES_IMAGES_FEATURES": json.dumps(
                    ['filename_resized_image', 'filename_objects_image', 'filename_surfaces_image']),
            }
        }
        # Crear y ejecutar el contenedor
        container = dockerClient.containers.run(**options)
    container_data = {}
    if container:
        data = {}
        data["id"] = container.id
        data["status"] = container.attrs["State"]["Status"]
        data["short_id"] = container.short_id
        data["name"] = container.attrs["Name"]
        data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
        data["image"] = container.attrs["Config"]["Image"]
        data["params"] = container.attrs["Config"]["Env"]
        container_data = data
        return {"container": container_data}
    return {"success": False}, 400


@app.get("/real-system/info")
async def real_system_info():
    id_container = container_real_system_name
    try:
        container = dockerClient.containers.get(id_container)
        if not container:
            raise HTTPException(status_code=404, detail="Container not available")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Container not available")
    data = {}
    data["id"] = container.id
    data["status"] = container.attrs["State"]["Status"]
    data["state"] = container.attrs["State"]
    data["short_id"] = container.short_id
    data["name"] = container.attrs["Name"]
    data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
    data["image"] = container.attrs["Config"]["Image"]
    data["params"] = container.attrs["Config"]["Env"]
    data["created"] = container.attrs["Created"]

    try:
        dataQueriesMongo = dmQueries.findDigitalModelByIdMongo(id_container)
        data["mongo"] = dataQueriesMongo
    except Exception as e:
        print(e)

    digital_model = data
    return {"real_system": digital_model, "docker": True}


@app.post("/real-system/stop")
async def real_system_stop():
    id_container = container_real_system_name
    container = dockerClient.containers.get(id_container)
    # Parar el contenedor
    container.stop()
    return {"success": True}


@app.get("/digital-models/info/{id_container}")
async def digital_model_info(id_container):
    container = dockerClient.containers.get(id_container)
    digital_model = None
    if not container:
        raise HTTPException(status_code=404, detail="Container not available")
    data = {}
    data["id"] = container.id
    data["status"] = container.attrs["State"]["Status"]
    data["state"] = container.attrs["State"]
    data["short_id"] = container.short_id
    data["name"] = container.attrs["Name"]
    data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
    data["image"] = container.attrs["Config"]["Image"]
    data["params"] = container.attrs["Config"]["Env"]
    data["created"] = container.attrs["Created"]

    try:
        dataQueriesMongo = dmQueries.findDigitalModelByIdMongo(id_container)
        data["mongo"] = dataQueriesMongo
    except Exception as e:
        print(e)

    digital_model = data
    return {"digital_model": digital_model, "docker": True}


@app.post("/digital-models/start/{id_container}")
async def digital_models_start(id_container):
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.get(id_container)
    container.start()
    return {"success": True}


@app.post("/digital-models/stop/{id_container}")
async def digital_models_stop(id_container):
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.get(id_container)
    container.stop()
    return {"success": True}


@app.post("/digital-models/delete/{id_container}")
async def digital_models_delete(id_container):
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.get(id_container)
    container.remove()
    return {"success": True}


@app.get("/real-system/query/")
async def real_system_query(query=""):
    # Crear y ejecutar el contenedor
    id_container = container_real_system_name
    container = dockerClient.containers.get(id_container)
    status = container.attrs["State"]["Status"]
    ports = container.attrs['NetworkSettings']['Ports']
    if status == "running":
        ip_address = container.attrs["NetworkSettings"]["IPAddress"]
        port_api = ports["8001/tcp"][0]["HostPort"]
        response = requests.get(f"http://127.0.0.1:{port_api}{query}", timeout=20)
        data = response.json()

        if "actual_evaluation_dict" in str(query):
            dmQueries.addOrUpdateDigitalModelMongo(id_container, data)

        return {"data": data, "docker": True}
    else:
        raise HTTPException(status_code=400, detail="Container not available")


@app.get("/digital-models/query/{id_container}")
async def digital_models_query(id_container, query=""):
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.get(id_container)
    status = container.attrs["State"]["Status"]
    ports = container.attrs['NetworkSettings']['Ports']
    if status == "running":
        ip_address = container.attrs["NetworkSettings"]["IPAddress"]
        port_api = ports["8001/tcp"][0]["HostPort"]
        response = requests.get(f"http://127.0.0.1:{port_api}{query}", timeout=20)
        data = response.json()

        if "actual_evaluation_dict" in str(query):
            dmQueries.addOrUpdateDigitalModelMongo(id_container, data)

        return {"data": data, "docker": True}
    else:
        raise HTTPException(status_code=400, detail="Container not available")


@app.post("/digital-models/predict/{id_container}/multiple")
async def digital_models_predict_multiple(id_container, fileCSV: UploadFile):
    contents = await fileCSV.read()
    data = None
    samplesJson = None
    evaluation_dict = None

    df = pd.read_csv(io.BytesIO(contents))

    container = dockerClient.containers.get(id_container)
    status = container.attrs["State"]["Status"]
    ports = container.attrs['NetworkSettings']['Ports']
    if status == "running":
        ip_address = container.attrs["NetworkSettings"]["IPAddress"]
        port_api = ports["8001/tcp"][0]["HostPort"]
        response = requests.post(f"http://127.0.0.1:{port_api}/predict_multiple", json=df.to_json(), timeout=20)
        samplesJson = response.json()
        response = requests.post(f"http://127.0.0.1:{port_api}/evaluate_dataframe", json=df.to_json(), timeout=20)
        evaluation_dict = response.json()

    return {"samples": samplesJson, "evaluation_dict": evaluation_dict}


@app.post("/digital-models/predict/{id_container}/single")
async def digital_models_predict_single(id_container, info: Request, resizedImage: UploadFile, objectImage: UploadFile,
                                        surfaceImage: UploadFile):
    info_json = await info.form()
    contentsResizedImage = await resizedImage.read()
    contentsObjectImage = await objectImage.read()
    contentsSurfaceImage = await surfaceImage.read()
    data = None
    sample_response = None

    container = dockerClient.containers.get(id_container)
    status = container.attrs["State"]["Status"]
    ports = container.attrs['NetworkSettings']['Ports']
    if status == "running":
        ip_address = container.attrs["NetworkSettings"]["IPAddress"]
        port_api = ports["8001/tcp"][0]["HostPort"]
        sampleJson = {
            "resizedImage": base64.b64encode(contentsResizedImage).decode("utf-8"),
            "objectImage": base64.b64encode(contentsObjectImage).decode("utf-8"),
            "surfaceImage": base64.b64encode(contentsSurfaceImage).decode("utf-8"),
            "speed": info_json["speed"],
            "rotation_rate_z": info_json["rotation_rate_z"],
            "channel_camera": info_json["channel_camera"],
            "anomaly": True
        }
        response = requests.post(f"http://127.0.0.1:{port_api}/predict_single", json=sampleJson, timeout=20)
        data = response.json()

    return data


@app.post("/real-system/replace-model/{id_container}")
async def real_system_replace_model(id_container: str):
    success = False
    container_digital_model = dockerClient.containers.get(id_container)
    container_real_system = dockerClient.containers.get(container_real_system_name)

    status_real_system = container_real_system.attrs["State"]["Status"]
    status_digital_model = container_digital_model.attrs["State"]["Status"]

    if status_real_system == "running" and status_digital_model == "running":
        ports_real_system = container_real_system.attrs['NetworkSettings']['Ports']
        ports_digital_model = container_digital_model.attrs['NetworkSettings']['Ports']
        port_api_real_system = ports_real_system["8001/tcp"][0]["HostPort"]
        port_api_digital_model = ports_digital_model["8001/tcp"][0]["HostPort"]

        print("QUERY: ACTUAL MODEL FILE")
        query_actual_model_file = "/actual_model_file"
        response = requests.get(f"http://127.0.0.1:{port_api_digital_model}{query_actual_model_file}", timeout=20)
        model_bytes = response.content
        print(type(model_bytes))

        print("QUERY: ACTUAL EVALUATION DICT")
        query_evaluation_dict = "/actual_evaluation_dict"
        response = requests.get(f"http://127.0.0.1:{port_api_digital_model}{query_evaluation_dict}", timeout=20)
        evaluation_dict = response.json()["evaluation_dict"]
        # print("evaluation_dict: " + str(evaluation_dict))
        print(type(evaluation_dict))

        print("QUERY: REPLACE ACTUAL MODEL")
        query_post_replace_model = "/replace_actual_model"
        headers = {"Content-Type": "multipart/form-data"}
        model_bytes = b"contenido del archivo"
        response = requests.post(f"http://127.0.0.1:8081{query_post_replace_model}", files={"model_bytes": model_bytes},
                                 data={"evaluation_dict": json.dumps(evaluation_dict)},  timeout=20)
        success = response.json()
        print("RESPONSE: " + str(success))
        success = success.get("success", False)

    return {"success": success}


@app.post("/digital-models/combine-models")
async def digital_models_combine_models(info: Request):
    info_json = await info.json()
    list_id_containers = info_json["digital-models-selected"]

    models_json = []
    for id_container in list_id_containers:
        container_digital_model = dockerClient.containers.get(id_container)
        status_digital_model = container_digital_model.attrs["State"]["Status"]
        ports_digital_model = container_digital_model.attrs['NetworkSettings']['Ports']
        port_api_digital_model = ports_digital_model["8001/tcp"][0]["HostPort"]
        query_actual_model_file = "/actual_model_json"
        response = requests.get(f"http://127.0.0.1:{port_api_digital_model}{query_actual_model_file}", timeout=20)
        model_json = response.json()
        models_json.append(model_json)

    container_name = info_json["container_name"]
    options = {
        "image": f"{image_digital_model_name}:{image_digital_model_tag}",
        "name": container_name,
        "detach": True,  # Ejecutar el contenedor en segundo plano
        "ports": {"8001/tcp": None},
        "environment": {
            "DIGITAL_MODEL_NAME": container_name,
            "DIGITAL_MODEL_COMBINE_MODEL_CONFIGS": json.dumps(models_json),
            "DIGITAL_MODEL_USERNAME_OWNER": info_json["DIGITAL_MODEL_USERNAME_OWNER"],
            "DIGITAL_MODEL_RETRAINING_TEST_SIZE": float(0.25),
            "DIGITAL_MODEL_RETRAINING_TUNNING": int(0),
            "DIGITAL_MODEL_RETRAINING_MIN_SPLIT": int(2000),
            "DIGITAL_MODEL_RETRAINING_MAX_SPLIT": int(5000),
            "DIGITAL_MODEL_RETRAINING_MIN_EPOCHS": int(10),
            "DIGITAL_MODEL_RETRAINING_MAX_EPOCHS": int(20),
            "DIGITAL_MODEL_RETRAINING_BEST_EPOCH": int(0),
            "DIGITAL_MODEL_RETRAINING_RETRAIN_WEIGHTS": int(1),
            "DIGITAL_MODEL_RETRAINING_RANDOM_SAMPLES": int(1),
            "DIGITAL_MODEL_SIZE_IMAGES_WIDTH": int(80),
            "DIGITAL_MODEL_SIZE_IMAGES_HEIGHT": int(45),
            "DIGITAL_MODEL_THRESHOLD_ANOMALY": float(0.5),
            "DIGITAL_MODEL_SIZE_IMAGES_OPTIMIZER": "adam",
            "DIGITAL_MODEL_SIZE_IMAGES_LOSS": "binary_crossentropy",
            "DIGITAL_MODEL_SIZE_IMAGES_METRICS": json.dumps(['accuracy', 'f1_score', 'recall', 'precision']),
            "DIGITAL_MODEL_SIZE_IMAGES_METRIC_OBJECTIVE": info_json["DIGITAL_MODEL_SIZE_IMAGES_METRIC_OBJECTIVE"],
            "DIGITAL_MODEL_SIZE_IMAGES_FLOAT_FEATURES": json.dumps(['channel_camera', 'speed', 'rotation_rate_z']),
            "DIGITAL_MODEL_SIZE_IMAGES_IMAGES_FEATURES": json.dumps(
                ['filename_resized_image', 'filename_objects_image', 'filename_surfaces_image']),
        }
    }
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.run(**options)
    container_data = {}
    if container:
        data = {}
        data["id"] = container.id
        data["status"] = container.attrs["State"]["Status"]
        data["short_id"] = container.short_id
        data["name"] = container.attrs["Name"]
        data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
        data["image"] = container.attrs["Config"]["Image"]
        data["params"] = container.attrs["Config"]["Env"]
        container_data = data
        return {"container": container_data}

    return {}


@app.post("/users/register")
async def users_register(info: Request):
    info_json = await info.form()
    username = info_json["username"]
    password1 = info_json["password1"]
    password2 = info_json["password2"]
    assert password1 == password2

    passwordHashed = hashlib.md5(password1.encode()).hexdigest()

    userExistent = userQueries.getUserByUsername(username)
    if userExistent:
        raise HTTPException(status_code=400, detail="User already exists")

    userJson = {
        "username": username,
        "password": passwordHashed,
        "createdAt": datetime.datetime.now(),
        "lastLoginAt": datetime.datetime.now()
    }
    result = userQueries.addNewUser(userJson)
    return json.loads(MongoJSONEncoder().encode(userJson))


@app.post("/users/login")
async def users_login(info: Request):
    info_json = await info.form()
    username = info_json["username"]
    password = info_json["password"]

    passwordHashed = hashlib.md5(password.encode()).hexdigest()

    userExistent = userQueries.getUserByUsername(username)
    if not userExistent:
        raise HTTPException(status_code=400, detail="User not exists")

    if passwordHashed != userExistent["password"]:
        raise HTTPException(status_code=400, detail="Wrong password")
    return json.loads(MongoJSONEncoder().encode(userExistent))


if __name__ == "__main__":
    try:
        ip = "0.0.0.0"
        port = "8080"
        uvicorn.run(app, host=ip, port=int(port))
    except Exception as e:
        logging.exception("Error en API: " + str(e))
