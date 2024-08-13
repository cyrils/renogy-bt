import json
import logging
import requests
import paho.mqtt.publish as publish
from configparser import ConfigParser
from datetime import datetime

PVOUTPUT_URL = 'http://pvoutput.org/service/r2/addstatus.jsp'

class DataLogger:
    def __init__(self, config: ConfigParser):
        self.config = config

    def log_remote(self, json_data):
        headers = { "Authorization" : f"Bearer {self.config['remote_logging']['auth_header']}" }
        req = requests.post(self.config['remote_logging']['url'], json = json_data, timeout=15, headers=headers)
        logging.info("Log remote 200") if req.status_code == 200 else logging.error(f"Log remote error {req.status_code}")

    def create_mqtt(self, json_data):
        logging.info(f"mqtt create")
        user = self.config['mqtt']['user']
        password = self.config['mqtt']['password']
        auth = None if not user or not password else {"username": user, "password": password}

        for data in json_data['device_info']:

            device_class = json.dumps(json_data['device_info'][data]['device_class']);
            device_class = device_class.replace("\"","")
            unit_of_measurement = json.dumps(json_data['device_info'][data]['unit_of_measurement'])
            unit_of_measurement = unit_of_measurement.replace("\"","")

            arrJSON = {}
            arrJSON['name'] = data
            arrJSON['state_topic'] = self.config['mqtt']['topic']+"/"+data+"/status"
            if device_class != "":
                arrJSON['device_class'] = device_class
                arrJSON['unit_of_measurement'] = unit_of_measurement
            arrJSON['unique_id'] = "unique_teste_status_"+data
            arrJSON['object_id'] = "renogy_"+data
            arrJSON['icon'] = "mdi:desktop-classic"
            arrJSON['device'] = {}
            arrJSON['device']['name'] = 'Renogy BT'
            arrJSON['device']['identifiers'] = self.config['device']['alias']

            publish.single(
                self.config['mqtt']['hainstance']+"/sensor/"+self.config['device']['alias']+"/"+data+"/config", payload=json.dumps(arrJSON),
                hostname=self.config['mqtt']['server'], port=self.config['mqtt'].getint('port'),
                auth=auth, client_id="renogy-bt"
            )

    def log_mqtt(self, json_data):
        logging.info(f"mqtt logging")
        user = self.config['mqtt']['user']
        password = self.config['mqtt']['password']
        auth = None if not user or not password else {"username": user, "password": password}

        for data in json_data['device_info']:
            publish.single(
                self.config['mqtt']['topic']+"/"+data+"/status", payload=json.dumps(json_data['device_info'][data]['value']),
                hostname=self.config['mqtt']['server'], port=self.config['mqtt'].getint('port'),
                auth=auth, client_id="renogy-bt"
            )

    def log_pvoutput(self, json_data):
        date_time = datetime.now().strftime("d=%Y%m%d&t=%H:%M")
        data = f"{date_time}&v1={json_data['power_generation_today']}&v2={json_data['pv_power']}&v3={json_data['power_consumption_today']}&v4={json_data['load_power']}&v5={json_data['controller_temperature']}&v6={json_data['battery_voltage']}"
        response = requests.post(PVOUTPUT_URL, data=data, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Pvoutput-Apikey": self.config['pvoutput']['api_key'],
            "X-Pvoutput-SystemId":  self.config['pvoutput']['system_id']
        })
        print(f"pvoutput {response}")		
