import json
import logging
import requests
import gspread
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

    def log_mqtt(self, json_data):
        logging.info(f"mqtt logging")
        user = self.config['mqtt']['user']
        password = self.config['mqtt']['password']
        auth = None if not user or not password else {"username": user, "password": password}

        publish.single(
            self.config['mqtt']['topic'], payload=json.dumps(json_data),
            hostname=self.config['mqtt']['server'], port=self.config['mqtt'].getint('port'),
            auth=auth,
            client_id="renogy-bt"
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

    def is_first_row_empty(worksheet):
        return len(worksheet.row_values(1)) == 0

    def log_google_sheets(self, json_data):
        now = datetime.now()
        dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
        sheet_id = self.config['google_sheets']['sheet_id']
        worksheet_name = self.config['google_sheets']['worksheet_name']
        credentials_file = self.config['google_sheets']['credentials_file']
        sa = gspread.service_account(filename=credentials_file)
        sh = sa.open_by_key(sheet_id)
        wks = sh.worksheet(worksheet_name)
        output = json_data
        values = [dt_string] + list(output.values())
        if DataLogger.is_first_row_empty(wks):
          keys = ["Date/Time"] + list(output.keys())
          wks.append_row(keys)
        wks.append_row(values)
