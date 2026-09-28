import requests
import time
import sys
import json
import random
import csv
import os
import socket

BG_BLACK = "\033[40m"
GREEN = "\033[32m"
RESET = "\033[0m"
BOLD = "\033[1m"

from cryptography.fernet import Fernet
from misc.crypto import CryptoManager


def save_performance(client, data):
    filename = f"./performance/{client}.csv"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not os.path.isfile(filename):
            writer.writerow(
                [
                    "Timestamp",
                    "Layers",
                    "Scenario",
                    "Client",
                    "Latenza_Avg",
                    "Richieste",
                    "Proxy_Chain",
                ]
            )
        writer.writerow(data)


def no_proxy(config, client, path, iterazioni):
    timestamp = time.time()
    time.sleep(2)
    server = config.get("server_ip")

    url = f"http://{server}:80/"

    crypto = CryptoManager()
    try:
        crypto.load_public_key("server_public.pem")
    except:
        print("Manca chiave pubblica!")
        return

    session_key = crypto.generate_fernet_key()
    cipher = Fernet(session_key)

    real_request = {
        "method": "GET",
        "path": f"{path}",
    }

    encrypted_http = cipher.encrypt(json.dumps(real_request).encode()).hex()
    enc_key = crypto.encrypt_rsa(session_key).hex()
    payload = {"message": encrypted_http, "key": enc_key}

    latencies = []

    for i in range(iterazioni):
        print(f"[>] Iterazione {i+1} di {client} iniziata.")
        start_time = time.time()
        try:
            response = requests.post(url, json=payload)
            end_time = time.time()

            if response.status_code == 200:
                dec_resp = cipher.decrypt(bytes.fromhex(response.text)).decode()
                resp_json = json.loads(dec_resp)
                print(
                    f"[Risposta del server {server} - Status: {resp_json.get('status')}]"
                )
                print(resp_json.get("body"))
                latency = end_time - start_time
                latencies.append(latency)

            else:
                print(
                    f"[>] Richiesta del client {client} fallita: Errore HTTP {response.status_code} - {response.text}"
                )
        except requests.exceptions.RequestException as e:
            print(f"[>] Errore: {e}")

    if len(latencies) > 0:
        avg = sum(latencies) / len(latencies)
    else:
        avg = 0

    row = [
        timestamp,
        config.get("num_layers"),
        config.get("scenario"),
        client,
        f"{avg:.4f}",
        iterazioni,
        [],
    ]
    save_performance(client, row)


def run(client, path, iterazioni):
    with open("config.json", "r") as f:
        config = json.load(f)
    scenario = config.get("scenario")
    timestamp = time.time()
    if scenario == 5:
        no_proxy(config, client, path, iterazioni)
        return

    latencies = []
    log_chain = []
    for i in range(iterazioni):
        proxies = config.get(f"proxy_list", [])
        server = config.get("server_ip")
        layers = config.get("num_layers")
        num_proxies = config.get("num_proxies")

        if scenario == 4:
            all_chains = config.get(f"proxy_{client}", [])
            proxy_chain = list(all_chains[i])
        else:
            proxy_chain = random.sample(proxies, num_proxies)

        log_chain.append(list(proxy_chain))

        print(f"[>] Uso {len(proxy_chain)} server proxy")
        print("[>] Proxy Chains generate")
        for idx, p in enumerate(proxy_chain):
            if idx == len(proxy_chain) - 1:
                print(p)
            else:
                print(p, end=" -> ")

        first_hop = proxy_chain.pop(0)
        url = f"http://{first_hop}:80/proxy"

        crypto = CryptoManager()
        try:
            crypto.load_public_key("server_public.pem")
        except:
            print("Manca chiave pubblica!")
            return

        session_key = crypto.generate_fernet_key()
        cipher = Fernet(session_key)

        real_request = {
            "method": "GET",
            "path": f"{path}",
        }

        encrypted_http = cipher.encrypt(json.dumps(real_request).encode()).hex()
        enc_key = crypto.encrypt_rsa(session_key).hex()

        payload = {
            "routing": {
                "current_proxy": first_hop,
                "proxy_chain": proxy_chain,
                "server_ip": server,
            },
            "message": encrypted_http,
            "key": enc_key,
        }

        print(f"[>] Iterazione {i+1} di {client} iniziata.")
        start_time = time.time()
        try:
            response = requests.post(url, json=payload)
            end_time = time.time()

            if response.status_code == 200:
                dec_resp = cipher.decrypt(bytes.fromhex(response.text)).decode()
                resp_json = json.loads(dec_resp)
                print(
                    f"[Risposta del server {server} - Status: {resp_json.get('status')}]"
                )
                print(resp_json.get("body"))
                latency = end_time - start_time
                latencies.append(latency)

            else:
                print(
                    f"[>] Richiesta del client {client} fallita: Errore HTTP {response.status_code} - {response.text}"
                )
        except requests.exceptions.RequestException as e:
            print(f"[>] Errore: {e}")

    if not latencies:
        return

    if len(latencies) > 0:
        avg = sum(latencies) / len(latencies)
    else:
        avg = 0

    row = [
        timestamp,
        layers,
        scenario,
        client,
        f"{avg:.2f}",
        iterazioni,
        str(log_chain),
    ]
    save_performance(client, row)


if __name__ == "__main__":
    print(f"{BG_BLACK}{GREEN}{BOLD}", end="")
    if len(sys.argv) < 4:
        print("[>] Uso errato, devi usare [client_name path_server n_iterazioni]")
        sys.exit(1)
    else:
        client = sys.argv[1]
        path = sys.argv[2]
        iterazioni = sys.argv[3]

    run(client, path, int(iterazioni))
    print(RESET, end="")
    sys.stdout.flush()
