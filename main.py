from fastapi import FastAPI, HTTPException
import uvicorn
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import logging
import docker
import uuid
import requests


app = FastAPI(middleware=[
    Middleware(CORSMiddleware, allow_origins=["*"])
])
dockerClient = docker.from_env()

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
    image_name = "mdv2"
    containers = dockerClient.containers.list(all=True, filters={"ancestor": image_name})
    digital_models = []
    for container in containers:
        data = {}
        data["id"] = container.id
        data["status"] = container.attrs["State"]["Status"]
        data["short_id"] = container.short_id
        data["name"] = container.attrs["Name"]
        data["ip"] = container.attrs["NetworkSettings"]["IPAddress"]
        data["image"] = container.attrs["Config"]["Image"]
        data["params"] = container.attrs["Config"]["Env"]
        digital_models.append(data)
    return {"digital_models": digital_models}

@app.get("/all_real_systems")
async def all_real_systems():
    image_name = "rsv2"
    containers = dockerClient.containers.list(all=True, filters={"ancestor": image_name})
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

@app.get("/digital-models/new")
async def digital_models_new():
    image_name = "mdv2"
    container_name = "mdv2-" + str(uuid.uuid1())
    options = {
        "image": image_name,
        "name": container_name,
        "detach": True,  # Ejecutar el contenedor en segundo plano
        "ports": {"8001/tcp": None}
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

@app.get("/digital-models/start/{id_container}")
async def digital_models_start(id_container):
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.get(id_container)
    container.start()
    return {"success": True}

@app.get("/digital-models/stop/{id_container}")
async def digital_models_start(id_container):
    # Crear y ejecutar el contenedor
    container = dockerClient.containers.get(id_container)
    container.stop()
    return {"success": True}

@app.get("/digital-models/delete/{id_container}")
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

if __name__ == "__main__":
    try:
        ip = "0.0.0.0"
        port = "8080"
        uvicorn.run(app, host=ip, port=int(port))
    except Exception as e:
        logging.exception("Error en API: " + str(e))
