import json
import logging
import os
import time

from kubernetes import client, config

import cpu_manager_policy

INTERVAL = os.getenv("INTERVAL", 60)
NODE_META_FILE = "/etc/cds/node-meta"

logging.basicConfig(level=logging.INFO)

def load_kubernetes_config():
    try:
        logging.info("Loading incluster kubernetes config")
        config.load_incluster_config()
    except Exception as e:
        logging.warning(f"failed to load incluster kubernetes config{e}")
        logging.info("Loading incluster kubernetes config")
        try:
            config.load_kube_config()
        except Exception as e:
            logging.fatal(f"failed to load incluster kubernetes config{e}")



def get_node_id(filename: str):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            return data["node_id"]
    except Exception as e:
        logging.error(f"Error occurred while reading node meta file {filename}:", str(e))
    return ""


def scan_node_annotations(node_id: str):
    api = client.CoreV1Api()
    try:
        nodes = api.list_node().items
        for node in nodes:
            if node.spec.provider_id == node_id:
                return node.metadata.annotations or {}
    except Exception as e:
        logging.error("Error occurred while reading Kubernetes Node Annotation:", str(e))
    return {}


def run_config_jobs(annotations: dict):
    cpu_manager_policy.config(annotations)
    # TODO: add other jobs below if needed in the future


def main():
    node_id = get_node_id(NODE_META_FILE)
    load_kubernetes_config()
    while True:
        annotations = scan_node_annotations(node_id)
        run_config_jobs(annotations)
        time.sleep(int(INTERVAL))


if __name__ == "__main__":
    main()
