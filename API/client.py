import requests, uuid
import API.config as FuniCFG
from funi_cfg import LOGIN_DATA

def LOGIN(SESSION):
    resp = SESSION.post(url=FuniCFG.ENDPOINTS["LOGIN"], headers=FuniCFG.LOGIN_HEADERS, data={"username":LOGIN_DATA["EMAIL"],"password":LOGIN_DATA["PASS"]})#.json()
    if int(resp.status_code) > 200:
        print(resp.json()["error"])
        exit()
    return resp.json()["token"], resp.json()['user']['id']
    
