import requests


class Kong:
    def __init__(self, host):
        self.kong_host = host

    def get_services(self):
        url = self.kong_host + "/services"
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get services: {response.status_code}, {response.text}")

    def get_routes(self):
        url = self.kong_host + "/routes"
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get routes: {response.status_code}, {response.text}")

    def add_service(self, name, url):
        kong_url = self.kong_host + "/services"
        payload = {
            "name": name,
            "url": url
        }
        response = requests.post(kong_url, json=payload)

        if response.status_code == 201:
            return response.json()  # Service created
        else:
            raise Exception(f"Failed to add service: {response.status_code}, {response.text}")

    def add_route(self, service_id, name,path):
        url = self.kong_host + "/routes"
        payload = {
            "paths": [path],
            "name": name,
            "service": {"id": service_id}
        }
        response = requests.post(url, json=payload)

        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to add route: {response.status_code}, {response.text}")
