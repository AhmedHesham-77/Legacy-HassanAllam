import os
import requests


class AppspaceRequests:
    def __init__(self):
        self.post_headers = {
            'Content-Type': 'application/json',
            'Host': 'preview.nexusondemand.com',
            'Content-Length': '85',
            'Connection': 'keep-alive',
        }
        self.post_body = {
            "Authentication": {
                "Username": os.getenv('APPSPACE_USERNAME'),
                "Password": os.getenv('APPSPACE_PASSWORD')
            }
        }
        self.get_headers = {
            'content-type': 'application/json',
            'accept': 'application/json'
        }
        self.appspace_host = os.getenv('APPSPACE_HOST')

    def get_token(self):
        token_xml = requests.post(f'http://{self.appspace_host}/api/v1/token/request', json=self.post_body,
                                  headers=self.post_headers)
        return token_xml

    def get_groups_data(self):
        players_groups = requests.get(f'http://{self.appspace_host}/api/v1/core/devices/groups',
                                      headers=self.get_headers)
        groups = players_groups.json().get('Groups')
        return groups

    def get_devices_data(self):
        players = requests.get(f'http://{self.appspace_host}/api/v1/core/devices?rpp=250', headers=self.get_headers)
        devices_data = players.json().get('Devices')
        return devices_data
