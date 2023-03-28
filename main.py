from fastapi import FastAPI, Request, HTTPException, Form
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
from queries.MongoJSONEncoder import MongoJSONEncoder

app = FastAPI(middleware=[
    Middleware(CORSMiddleware, allow_origins=["*"])
])
dockerClient = docker.from_env()

image_digital_model_name = "jesuscumpli/model-digital"
image_digital_model_tag = "mdv3"
image_real_sytem_name = "jesuscumpli/real-system"
image_real_system_tag = "rsv2"


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/all_containers")
async def all_containers():
    containers = dockerClient.containers.list(all=True)
    print(containers)
    list_containers = []
    for container in containers:
        data = {}
        data["id"] = container.id
        data["short_id"] = container.short_id
        data["name"] = container.attrs["Name"]
        data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
        data["image"] = container.attrs["Config"]["Image"]
        data["params"] = container.attrs["Config"]["Env"]
        list_containers.append(data)
    return {"containers": list_containers}


@app.get("/all_containers_by_image_name/{ancestor}")
async def all_containers_by_image_name(ancestor):
    containers = dockerClient.containers.list(all=True, filters={"ancestor": ancestor})
    print(containers)
    list_containers = []
    for container in containers:
        data = {}
        data["id"] = container.id
        data["short_id"] = container.short_id
        data["name"] = container.attrs["Name"]
        data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
        data["image"] = container.attrs["Config"]["Image"]
        data["params"] = container.attrs["Config"]["Env"]
        list_containers.append(data)
    return {"containers": list_containers}


@app.get("/all_images")
async def all_images():
    images = dockerClient.images.list(all=True)
    print(images)
    list_images = []
    for image in images:
        data = {}
        data["id"] = image.id
        data["short_id"] = image.short_id
        data["tags"] = image.tags
        data["labels"] = image.labels
        data["attrs"] = image.attrs
        list_images.append(data)
    return {"images": list_images}


@app.get("/digital-models/all")
async def all_digital_models():
    containers = dockerClient.containers.list(all=True, filters={
        "ancestor": f"{image_digital_model_name}:{image_digital_model_tag}"})
    digital_models = []
    for container in containers:
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
        digital_models.append(data)
    return {"digital_models": digital_models}


@app.get("/all_real_systems")
async def all_real_systems():
    containers = dockerClient.containers.list(all=True,
                                              filters={"ancestor": f"{image_real_sytem_name}:{image_real_system_tag}"})
    real_systems = []
    for container in containers:
        data = {}
        data["id"] = container.id
        data["status"] = container.attrs["State"]["Status"]
        data["short_id"] = container.short_id
        data["name"] = container.attrs["Name"]
        data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
        data["image"] = container.attrs["Config"]["Image"]
        data["params"] = container.attrs["Config"]["Env"]
        real_systems.append(data)
    return {"real_systems": real_systems}


@app.post("/digital-models/new")
async def digital_models_new(info: Request):
    info_json = await info.form()
    container_name = info_json["container_name"]

    dockerClient.images.pull(repository=image_digital_model_name, tag=image_digital_model_tag)
    options = {
        "image": f"{image_digital_model_name}:{image_digital_model_tag}",
        "name": container_name,
        "detach": True,  # Ejecutar el contenedor en segundo plano
        "ports": {"8001/tcp": None},
        "environment": {
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

    digital_model = data
    return {"digital_model": digital_model}


@app.post("/digital-models/start/{id_container}")
async def digital_models_start(id_container):
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.get(id_container)
    container.start()
    return {"success": True}


@app.post("/digital-models/stop/{id_container}")
async def digital_models_start(id_container):
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


@app.get("/digital-models/query/{id_container}")
async def digital_models_query(id_container, query=""):
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.get(id_container)
    status = container.attrs["State"]["Status"]
    ports = container.attrs['NetworkSettings']['Ports']
    if status == "running":
        ip_address = container.attrs["NetworkSettings"]["IPAddress"]
        port_api = ports["8001/tcp"][0]["HostPort"]
        response = requests.get(f"http://127.0.0.1:{port_api}{query}")
        data = response.json()
        return {"data": data}
    else:
        raise HTTPException(status_code=400, detail="Container not available")


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
    return MongoJSONEncoder().encode(userJson)


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
    return MongoJSONEncoder().encode(userExistent)

if __name__ == "__main__":
    try:
        ip = "0.0.0.0"
        port = "8080"
        uvicorn.run(app, host=ip, port=int(port))
    except Exception as e:
        logging.exception("Error en API: " + str(e))
