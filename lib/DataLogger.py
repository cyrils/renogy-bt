import logging
import requests

class DataLogger:
    def __init__(self, config):
        self.config = config
        self.adapter_name = self.config['device']['adapter']
    
    def log_remote(self, json_data):
        req = requests.post(self.config['remote_logging']['url'], json = json_data, timeout=15)
        return req.status_code == 200

    def log_mqtt(self, json_data):
        logging.info(f"mqtt logging ${json_data}")
        return True