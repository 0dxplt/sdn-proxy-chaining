from flask import Flask, request
import requests
import json

app = Flask(__name__)

with open("config.json", "r") as f:
    server_ip = json.load(f).get("server_ip")


@app.route("/proxy", methods=["POST"])
def proxy_chain():
    data = request.json
    routing = data.get("routing", {})
    current_proxy = routing.get("current_proxy")
    proxy_chain = routing.get("proxy_chain", [])
    server_ip = routing.get("server_ip")
    message = data.get("message")
    key = data.get("key")

    print(f"[>] [{current_proxy}] Ricevuta richiesta. Hops rimanenti: {proxy_chain}")

    if len(proxy_chain) > 0:
        next_hop = proxy_chain.pop(0)
        url = f"http://{next_hop}:80/proxy"

        print(f"[>] [{current_proxy}] Inoltro a {next_hop}...")
        response = requests.post(
            url,
            json={
                "routing": {
                    "current_proxy": next_hop,
                    "proxy_chain": proxy_chain,
                    "server_ip": server_ip,
                },
                "message": message,
                "key": key,
            },
        )
        return response.content, response.status_code

    else:
        print(f"[>] [{current_proxy}] Inoltro al server {server_ip}...")

        data = {"message": message, "key": key}

        target_url = f"http://{server_ip}:80/"
        response = requests.post(
            target_url,
            json=data,
        )
        return response.content, response.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
