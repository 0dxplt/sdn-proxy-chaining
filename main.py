import subprocess
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.log import setLogLevel
from mininet.link import TCLink
import json
import os
import time
import random
import sys

from network.topology import Topology
from misc.crypto import CryptoManager


def config():
    print("[?] Scegli un numero (1-10) di livelli dell'architettura")
    try:
        value = input("[>] ")
        N = int(value)
    except ValueError:
        N = 3
    if N > 10 or N < 3:
        print("[>] Hai inserito un valore errato, imposto valore di default 3...")
        N = 3
        print(f"[>] Numero di layer dell'architettura: {N}")
    print("[?] Scegli un numero di iterazioni (1-10)")
    try:
        value = input("[>] ")
        iterazioni = int(value)
    except ValueError:
        iterazioni = 5
    if iterazioni > 10 or iterazioni < 1:
        print("[>] Hai inserito un valore errato, imposto valore di default 5...")
        iterazioni = 5
        print(f"[>] Numero di iterazioni: {iterazioni}")
    print("[?] Scegli il tipo di Scenario")
    print("[1] Traffico solo di H1")
    print("[2] Traffico H1, H2")
    print("[3] Traffico H1, H2, H3")
    print("[4] Traffico H1, H2, H3, con sovrapposizione proxy")
    print("[5] Traffico H1, H2, H3, senza utilizzo di proxy")
    try:
        value = input("[>] ")
        scenario = int(value)
    except ValueError:
        scenario = 3
    if scenario > 5 or scenario < 1:
        print("[>] Hai inserito un valore errato, imposto valore di default 3...")
        scenario = 3

    proxies = {}
    for i in range(1, N + 1):
        for j in range(1, 4):
            if i == 1:
                proxies[f"p_{i}_{j}"] = f"200.0.1.{j+1}"
            elif i == N:
                proxies[f"p_{i}_{j}"] = f"200.{N}.2.{j+1}"
            else:
                proxies[f"p_{i}_{j}"] = f"200.{i}.0.{j+1}"

    proxy_list = [ip for _, ip in proxies.items()]

    num_proxies = 6

    if scenario == 4:
        all_proxy_h1 = []
        all_proxy_h2 = []
        all_proxy_h3 = []

        for _ in range(iterazioni):
            proxy_h1 = []
            proxy_h2 = []
            proxy_h3 = random.sample(proxy_list, num_proxies)
            num_same = num_proxies // 2
            num_different = num_proxies - num_same
            common_part = random.sample(proxy_list, num_same)

            proxy_pool = [p for p in proxy_list if p not in common_part]
            proxy_h1 = random.sample(proxy_pool, num_different)
            proxy_h2 = [p for p in proxy_pool if p not in proxy_h1]
            proxy_h2 = random.sample(proxy_h2, num_different)

            proxy_h1 = common_part + proxy_h1
            proxy_h2 = common_part + proxy_h2

            all_proxy_h1.append(proxy_h1)
            all_proxy_h2.append(proxy_h2)
            all_proxy_h3.append(proxy_h3)

        file = {
            "num_layers": N,
            "num_proxies": num_proxies,
            "proxy_list": proxy_list,
            "server_ip": f"200.{N}.2.5",
            "scenario": scenario,
            "proxy_h_1_1": all_proxy_h1,
            "proxy_h_1_2": all_proxy_h2,
            "proxy_h_1_3": all_proxy_h3,
        }
    else:
        file = {
            "num_layers": N,
            "num_proxies": num_proxies,
            "proxy_list": proxy_list,
            "server_ip": f"200.{N}.2.5",
            "scenario": scenario,
        }
    with open("config.json", "w") as f:
        json.dump(file, f, indent=4)
    print('[>] Configurazioni salvate in "config.json"')
    logs = input("[?] Vuoi salvare i logs di output? (y/n): ").lower()
    if logs == "y" or logs == "Y":
        logs = True
    elif logs == "n" or logs == "N":
        logs = False
    else:
        logs = False

    return N, proxies, logs, scenario, iterazioni


def create_topology(N):
    net = Mininet(topo=Topology(N), link=TCLink, controller=RemoteController)
    print("[>] Topologia di rete creata")
    return net


def run(net, proxies, logs, scenario, tmux, iterazioni):
    net.start()
    print("[>] Rete Inizializzata")

    os.system("ryu-manager ryu.app.rest_router > /dev/null 2>&1 &")
    print("[>] Ryu Controller avviato")
    time.sleep(4)

    os.system("python3 network/routes.py > /dev/null 2>&1")
    print("[>] Rotte configurate")

    net.get("s1").cmd(f"rm ./logs/server/s1.log")
    if logs:
        net.get("s1").cmd("sudo python3 server.py > ./logs/server/s1.log &")
    else:
        net.get("s1").cmd("sudo python3 server.py &")
    print("[>] Server avviato")

    if scenario != 5:
        for name, _ in proxies.items():
            if name in net:
                net.get(name).cmd(f"rm ./logs/proxies/{name}.log")
                if logs:
                    net.get(name).cmd(
                        f"python3 -u proxy.py > ./logs/proxies/{name}.log 2>&1 &"
                    )
                else:
                    net.get(name).cmd(f"python3 -u proxy.py 2>&1 &")
                print(f"[>] Proxy {name} avviato")
        time.sleep(2)

    if scenario == 1:
        clients = ["h_1_1"]
    elif scenario == 2:
        clients = ["h_1_1", "h_1_2"]
    elif scenario == 3 or scenario == 4 or scenario == 5:
        clients = ["h_1_1", "h_1_2", "h_1_3"]

    tmux_panes = [1, 2, 3]
    active_processes = []

    for i, c_name in enumerate(clients):
        node = net.get(c_name)
        node.cmd(f"rm ./logs/clients/{c_name}.log")
        if tmux:
            pid = node.pid
            pane_id = tmux_panes[i]
            if logs:
                injection_cmd = f"sudo mnexec -a {pid} python3 client.py {c_name} /wnqiofnibybwyfbw {iterazioni} | tee ./logs/clients/{c_name}.log"
            else:
                injection_cmd = f"sudo mnexec -a {pid} python3 client.py {c_name} /wnqiofnibybwyfbw {iterazioni}"
            os.system(
                f"tmux send-keys -t proxy_chains:0.{pane_id} '{injection_cmd}' C-m"
            )
        else:
            cmd = f"sudo python3 -u client.py {c_name} /wnqiofnibybwyfbw {iterazioni}"
            p = node.popen(
                cmd,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            active_processes.append((c_name, p))
    if not tmux:
        if active_processes:
            for c_name, p in active_processes:
                output, _ = p.communicate()
                if logs:
                    with open(f"./logs/clients/{c_name}.log", "w") as f:
                        f.write(output)
                print(f"\n[{c_name}]")
                if output:
                    print(output.strip())

    input("\n[>>>] Premi INVIO per distruggere la simulazione e chiudere tutto...")
    net.stop()
    os.system("pkill -f ryu-manager")
    if tmux:
        os.system("tmux kill-session -t proxy_chains")


if __name__ == "__main__":
    if not os.path.exists("server_private.pem") or not os.path.exists(
        "server_public.pem"
    ):
        crypto = CryptoManager()
        crypto.generate_rsa_keys()
    os.system("clear")
    setLogLevel("error")
    print("[...] Effettuo il cleanup di Mininet")
    os.system("mn -c > /dev/null 2>&1")
    os.system("clear")
    N, proxies, logs, scenario, iterazioni = config()
    net = create_topology(N)
    if len(sys.argv) >= 2:
        if sys.argv[1] == "tmux":
            tmux = True
    else:
        tmux = False
    run(net, proxies, logs, scenario, tmux, iterazioni)
