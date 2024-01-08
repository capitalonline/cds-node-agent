import logging
import os
import subprocess

NODE_META_FILE = "/etc/cds/node-meta"
KUBELET_CONFIG_FILE = "/etc/systemd/system/kubelet.service.d/10-kubeadm.conf"
KUBELET_CPU_STATE_FILE = "/var/lib/kubelet/cpu_manager_state"
CPU_MANAGER_POLICY_ARG = "--cpu-manager-policy="
CPU_MANAGER_POLICY_ANNOTATION_KEY = "cds-node/cpu-manager-policy"

logging.basicConfig(level=logging.INFO)


def get_current_cpu_manager_policy_state(config_file: str):
    kv = ""
    try:
        with open(config_file, "r") as file:
            for line in file:
                if line.startswith("ExecStart=/usr/bin/kubelet"):
                    start = line.find(CPU_MANAGER_POLICY_ARG)
                    if start != -1:
                        end = line.find(" ", start)
                        if end == -1:
                            kv = line[start:]
                        else:
                            kv = line[start:end]
                        break
    except Exception as e:
        logging.error(f"Error occurred while reading kubelet config file {config_file}:", str(e))
    if kv == CPU_MANAGER_POLICY_ARG:
        return "none"
    else:
        current = kv[kv.find("="):].strip().strip("=")

    if current == "":
        return "none"
    return current


def update_config_file(config_file: str, target: str):
    contents = []
    try:
        with open(config_file, "r") as file:
            for line in file:
                if line.startswith("ExecStart=/usr/bin/kubelet"):
                    line = line.strip('\n')
                    start = line.find(CPU_MANAGER_POLICY_ARG)
                    if start != -1:
                        end = line.find(" ", start)
                        if end == -1:
                            key_value = line[start:]
                        else:
                            key_value = line[start:end]
                        if key_value == CPU_MANAGER_POLICY_ARG:
                            line = line.replace(CPU_MANAGER_POLICY_ARG, CPU_MANAGER_POLICY_ARG + target)
                        else:
                            line = line.replace(key_value, CPU_MANAGER_POLICY_ARG + target)
                    else:
                        line = line + " " + CPU_MANAGER_POLICY_ARG + target + "\n"
                    line = line + "\n"
                contents.append(line)
    except Exception as e:
        logging.error(f"Error occurred while reading kubelet config file {config_file}:", str(e))
    try:
        with open(config_file, "w") as file:
            file.writelines(contents)
    except Exception as e:
        logging.error(f"Error occurred while writing kubelet config file {config_file}:", str(e))


def delete_file(filename: str):
    if os.path.exists(filename):
        os.remove(filename)
    else:
        logging.error(f"file {filename} not exist")


def restart_kubelet():
    subprocess.run("systemctl daemon-reload".split(), capture_output=True)
    subprocess.run("systemctl restart kubelet".split(), capture_output=True)


def config(annotations):
    target = annotations.get("cds-node/cpu-manager-policy", "none")
    current = get_current_cpu_manager_policy_state(KUBELET_CONFIG_FILE)
    if target != current:
        logging.info(f"reconciling cpu manager policy, current:{current}, target:{target}")
        logging.info("updating kubelet config file")
        update_config_file(KUBELET_CONFIG_FILE, target)
        logging.info("deleting old CPU state file")
        delete_file(KUBELET_CPU_STATE_FILE)
        logging.info("restarting kubelet")
        restart_kubelet()
