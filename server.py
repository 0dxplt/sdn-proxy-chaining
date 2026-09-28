import threading
from flask import Flask, render_template, request
from scapy.all import sniff, wrpcap
import os
import json
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from cryptography.fernet import Fernet
from misc.crypto import CryptoManager

app = Flask(__name__)
PCAP_FILE = "server/traffic_s1.pcap"
IFACE = "s1-eth0"

crypto = CryptoManager()
if not os.path.exists("server_private.pem"):
    crypto.generate_rsa_keys()
else:
    crypto.load_keys()


def packet_sniffer():
    print(f"[>] Avvio sniffer su {IFACE}. Salvataggio su {PCAP_FILE}")
    pkts = sniff(iface=IFACE, filter="tcp port 80", count=20)
    wrpcap(PCAP_FILE, pkts, append=True)
    print(f"[>] Pacchetti salvati.")


@app.route("/", methods=["POST"])
def home():
    data = request.get_json(force=True)
    enc_key_hex = data.get("key")
    enc_payload_hex = data.get("message")

    session_key = crypto.decrypt_rsa(bytes.fromhex(enc_key_hex))
    cipher = Fernet(session_key)

    decrypted_json = cipher.decrypt(bytes.fromhex(enc_payload_hex)).decode()
    packet = json.loads(decrypted_json)

    target_path = packet.get("path")
    target_method = packet.get("method")
    target_body = packet.get("body")

    with app.test_client() as internal_client:
        internal_response = internal_client.open(
            path=target_path,
            method=target_method,
        )

        resp_data = internal_response.data
        resp_status = internal_response.status_code

    final_response_packet = {"status": resp_status, "body": resp_data.decode("utf-8")}

    encrypted_resp = cipher.encrypt(json.dumps(final_response_packet).encode()).hex()

    client_ip = request.remote_addr
    print(f"[>] Richiesta ricevuta da {client_ip}")
    return encrypted_resp, 200


@app.route("/wnqiofnibybwyfbw", methods=["GET"])
def secret():
    client_ip = request.remote_addr
    user_agent = request.headers.get("User-Agent", "Unknown")
    print(f"[>] Richiesta ricevuta da {client_ip}")
    return (
        render_template(
            "secret.html",
            client_ip=client_ip,
            user_agent=user_agent,
        ),
        200,
    )


if __name__ == "__main__":
    t = threading.Thread(target=packet_sniffer)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=80, debug=False)
    print("[>] Server Flask avviato")
