from datetime import datetime, timedelta
import random
import time
import logging
import docker
import requests
from queries.DigitalModels import queries as dmQueries
from queries.AlertsMessages import queries as alertsQueries
from constants import *
import json

logging.basicConfig(level=logging.INFO)
SLEEP_TIME = 60*5  # 5 minutes

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


if __name__ == "__main__":
    logging.info("START ALERTS SERVICE")
    dockerClient = docker.from_env()

    while True:
        try:
            logging.info("CHECKING ANOMALIES REAL SYSTEM")
            # Real System
            containerRealSystem = dockerClient.containers.get(container_real_system_name)
            port_api = containerRealSystem.attrs['NetworkSettings']['Ports']["8001/tcp"][0]["HostPort"]

            startDateTime = datetime.now() - timedelta(minutes=5)
            endDatetime = datetime.now()
            query = "/last_anomalies/" + str(startDateTime.strftime("%d-%m-%YT%H:%M")) + "/" + str(endDatetime.strftime("%d-%m-%YT%H:%M")) #01-05-2023T20:08
            # httpBackApi.get('/real-system/query', {params: {query: "/last_anomalies/" + startDatetime + "/" + endDatetime}});
            response = requests.get(f"http://127.0.0.1:{port_api}{query}", timeout=20)
            data = response.json()

            if not data or "anomalies" not in data:
                logging.info("REAL SYSTEM IS NOT RUNNING")
                time.sleep(SLEEP_TIME)
                continue

            anomalies = json.loads(data["anomalies"])
            if anomalies:
                logging.info("REAL SYSTEM - HAY ANOMALIAS: " + str(len(anomalies)))
                for anomaly in anomalies:
                    alertsQueries.addAlertAnomaly(anomaly)

        except Exception as e:
            logging.exception("Error en Federative Service: " + str(e))

        logging.info("SLEEPING...")
        time.sleep(SLEEP_TIME)
