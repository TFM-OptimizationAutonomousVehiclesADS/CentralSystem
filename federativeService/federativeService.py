import random
import time
import logging
import docker
import requests
from queries.DigitalModels import queries as dmQueries
from queries.AlertsMessages import queries as alertsQueries
from constants import *
import json

SLEEP_TIME = 120  # 2 minutes


def all_digital_models():
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
    return digital_models


def real_system_info():
    id_container = container_real_system_name
    try:
        container = dockerClient.containers.get(id_container)
        if not container:
            return None
    except Exception as e:
        print(e)
        return None
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

    if data["state"] != "running":
        return None
    return data


def real_system_replace_model(id_container: str):
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

        logging.info("QUERY: ACTUAL MODEL FILE")
        query_actual_model_file = "/actual_model_file"
        response = requests.get(f"http://127.0.0.1:{port_api_digital_model}{query_actual_model_file}", timeout=20)
        model_bytes = response.content
        logging.info(type(model_bytes))

        logging.info("QUERY: ACTUAL EVALUATION DICT")
        query_evaluation_dict = "/actual_evaluation_dict"
        response = requests.get(f"http://127.0.0.1:{port_api_digital_model}{query_evaluation_dict}", timeout=20)
        evaluation_dict = response.json()["evaluation_dict"]
        # print("evaluation_dict: " + str(evaluation_dict))
        logging.info(type(evaluation_dict))

        logging.info("QUERY: REPLACE ACTUAL MODEL")
        query_post_replace_model = "/replace_actual_model"
        response = requests.post(f"http://127.0.0.1:{port_api_real_system}{query_post_replace_model}",
                                 files={"model_bytes": model_bytes},
                                 data={"evaluation_dict": json.dumps(evaluation_dict)}, timeout=20)
        success = response.json()
        logging.info("RESPONSE: " + str(success))
        success = success.get("success", False)

    return success


if __name__ == "__main__":
    logging.info("START FEDERATIVE SERVICE")
    dockerClient = docker.from_env()

    exit(0)

    while True:
        try:
            logging.info("CHECKING METRICS OF REAL SYSTEM")
            # Real System
            containerRealSystem = dockerClient.containers.get(container_real_system_name)
            port_api = containerRealSystem.attrs['NetworkSettings']['Ports']["8001/tcp"][0]["HostPort"]
            query = "/actual_evaluation_dict"
            response = requests.get(f"http://127.0.0.1:{port_api}{query}", timeout=20)
            data = response.json()

            if not data or "evaluation_dict" not in data:
                logging.info("REAL SYSTEM IS NOT RUNNING")
                time.sleep(SLEEP_TIME)
                continue
            best_metric_real_system = data["evaluation_dict"]["f1_score"]

            logging.info("CHECKING METRICS OF DIGITAL MODELS")
            # Digital Models
            best_metric_found = 0.0
            best_digital_model_found = 0.0
            better_found = False
            allDigitalModels = all_digital_models()
            if allDigitalModels:
                for digitalModel in allDigitalModels:
                    try:
                        idDigitalModel = digitalModel["id"]
                        container = dockerClient.containers.get(idDigitalModel)
                        port_api = containerRealSystem.attrs['NetworkSettings']['Ports']["8001/tcp"][0]["HostPort"]
                        query = "/actual_evaluation_dict"
                        response = requests.get(f"http://127.0.0.1:{port_api}{query}", timeout=20)
                        data = response.json()
                        if data and "evaluation_dict" in data:
                            metric_result = data["evaluation_dict"]["f1_score"]
                            if metric_result > best_metric_real_system:
                                best_metric_found = metric_result
                                best_digital_model_found = digitalModel
                                better_found = True
                    except:
                        pass

            # Federative Technique
            if better_found:
                logging.info("SE HA ENCONTRAD UN MODELO DIGITAL CON MEJOR F1-SCORE")
                logging.info(f"Modelo Digital: {best_digital_model_found['name']}")
                logging.info(f"F1-SCORE: {best_metric_found}")

                replaced = real_system_replace_model(best_digital_model_found["id"])
                if replaced:
                    alertsQueries.addAlertMessage(
                        f"Se ha sustituido el ADS del sistema real por el ADS del modelo digital {best_digital_model_found['name']}",
                        "success")
                else:
                    logging.exception("No se ha podido reemplazar el modelo digital")

        except Exception as e:
            logging.exception("Error en Federative Service: " + str(e))

        time.sleep(SLEEP_TIME)
