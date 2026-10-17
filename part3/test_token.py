"""Find which token style gispc06 accepts. Run from the part3 folder:
    python test_token.py
Prints only OK / FAIL per variant. No token or password is printed."""
import os
import warnings

import requests
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

TOKEN_URL = os.environ["ARCGIS_TOKEN_URL"]
LAYER = os.environ["ARCGIS_LAYER_URL"]
USER = os.environ["ARCGIS_USERNAME"]
PWD = os.environ["ARCGIS_PASSWORD"]
REFERER = "https://gispc06"


def make_token(client):
    data = {"username": USER, "password": PWD, "expiration": 60, "f": "json", "client": client}
    if client == "referer":
        data["referer"] = REFERER
    body = requests.post(TOKEN_URL, data=data, verify=False, timeout=30).json()
    return body.get("token"), (body.get("error") or {}).get("message")


def try_layer(token, how, send_referer=False):
    headers, params = {}, {"f": "json"}
    if how == "header":
        headers["X-Esri-Authorization"] = f"Bearer {token}"
    else:
        params["token"] = token
    if send_referer:
        headers["Referer"] = REFERER
    body = requests.get(LAYER, params=params, headers=headers, verify=False, timeout=30).json()
    err = body.get("error")
    return ("OK  layer name = " + str(body.get("name"))) if not err else \
           f"FAIL {err.get('code')}: {err.get('message')}"


for client in ("requestip", "referer"):
    token, msg = make_token(client)
    if not token:
        print(f"[{client}] token request failed: {msg}")
        continue
    for how in ("header", "param"):
        print(f"[{client:9}] token via {how:6}: {try_layer(token, how, client == 'referer')}")