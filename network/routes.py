import requests
import json
import time

RYU_IP = "127.0.0.1"
RYU_PORT = "8080"
BASE_URL = f"http://{RYU_IP}:{RYU_PORT}/router"


def set_address(dpid, address):
    url = f"{BASE_URL}/{dpid}"
    print(f"Setting address {address} on Switch {dpid}...")
    r = requests.post(url, json={"address": address})
    if r.status_code != 200:
        print(f"Error: {r.text}")


def set_route(dpid, destination, gateway):
    url = f"{BASE_URL}/{dpid}"
    print(f"Setting route to {destination} via {gateway} on Switch {dpid}...")
    r = requests.post(url, json={"destination": destination, "gateway": gateway})
    if r.status_code != 200:
        print(f"Error: {r.text}")


def main():
    with open("config.json", "r") as f:
        N = json.load(f).get("num_layers")

    for i in range(1, N + 1):
        DPID = "{:016x}".format(i)
        if i == 1:
            set_address(DPID, "200.0.1.1/24")
            set_address(DPID, f"10.{i}.{i+1}.1/24")
        elif i == N:
            set_address(DPID, f"200.{N}.2.1/24")
            set_address(DPID, f"10.{i-1}.{i}.2/24")
        else:
            set_address(DPID, f"200.{i}.0.1/29")
            set_address(DPID, f"10.{i-1}.{i}.2/24")
            set_address(DPID, f"10.{i}.{i+1}.1/24")

        for j in range(1, N + 1):
            if i == j:
                continue

            if j == 1:
                set_route(DPID, "200.0.1.0/24", f"10.{i-1}.{i}.1")
            elif j == N:
                set_route(DPID, f"200.{j}.2.0/24", f"10.{i}.{i+1}.2")
            else:
                if j > i:
                    set_route(DPID, f"200.{j}.0.0/29", f"10.{i}.{i+1}.2")
                elif j < i:
                    set_route(DPID, f"200.{j}.0.0/29", f"10.{i-1}.{i}.1")


if __name__ == "__main__":
    main()
