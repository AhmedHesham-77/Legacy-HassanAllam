from shared.Classes.Functions import SpecialFunctions
from shared.Classes.Database import DatabaseFunctions
from starlette.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi import FastAPI
import logging
import os

# Logging configuration
log_file_path = '/appspace/appspace_players/logs/api.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a')
    ]
)

# Configration
players_json_file = '/appspace/appspace_players/json/players.json'
alarms_json_file = '/appspace/appspace_players/json/alarms.json'
functions = SpecialFunctions()
analysis_database_path = '/appspace/appspace_players/databases/analysis.db'
analysis_database = DatabaseFunctions(analysis_database_path)


class REST:
    def __init__(self):
        self.app = FastAPI()
        self.app.add_api_route("/devices", self.get_locations_data, methods=['GET'])
        self.app.add_api_route("/devices/location={location}", self.get_location_data, methods=['GET'])
        self.app.add_api_route("/devices/location={location}/device={device}", self.get_location_device_data,
                               methods=['GET'])
        self.app.add_api_route("/alarms", self.get_alarms, methods=["GET"])
        self.app.add_api_route("/alarms/host-alarms", self.get_host_alarm, methods=["GET"])
        self.app.add_api_route("/alarms/players-alarms", self.get_players_alarm, methods=["GET"])
        self.app.add_api_route("/analysis-file", self.get_analysis_file, methods=["GET"])
        self.app.add_api_route("/delete/analysis-file", self.delete_analysis_file, methods=["DELETE"])

    async def get_devices_data(self, data, devices_data=None):
        try:
            if devices_data is None:
                devices_data = {}
            for item, value in data.items():
                if isinstance(value, dict):
                    group_name = value.get('name').lower()
                    if 'devices' in value:
                        group_devices = value['devices']
                        if group_name in devices_data:
                            devices_data[group_name].update(group_devices)
                        else:
                            devices_data[group_name] = {'id': item, 'devices': group_devices}
                    elif item == 'devices':
                        devices_data[group_name].update(value)
                        devices_data.update(value)
                    else:
                        for subItem, subValue in value.items():
                            if isinstance(subValue, dict):
                                await self.get_devices_data(data=value, devices_data=devices_data)
            return devices_data
        except Exception as e:
            raise Exception(f"{e.args[0]}")

    async def get_locations_data(self):
        try:
            players_json_data = functions.read_json_data(players_json_file)
            locations_data = await self.get_devices_data(data=players_json_data)
            logging.info(f'Locations data fetched successfully')
            return JSONResponse(content=locations_data)
        except Exception as e:
            logging.exception(f'Error on get locations data function : {e.args[0]}')

    async def get_location_data(self, location):
        try:
            players_json_data = functions.read_json_data(players_json_file)
            locations_data = await self.get_devices_data(data=players_json_data)
            logging.info(f'Location {location} data fetched successfully')
            return JSONResponse(content=locations_data[location.lower()]['devices'])
        except Exception as e:
            logging.exception(f'Error on get location data function : {e.args[0]}')

    async def get_location_device_data(self, location, device):
        try:
            locations_data = await self.get_devices_data(data=players_json_data)
            logging.info(f'Device {device} data fro location {location} fetched successfully')
            return JSONResponse(content=locations_data[location.lower()]['devices'][device])
        except Exception as e:
            logging.exception(f'Error on get location device data function : {e.args[0]}')

    @staticmethod
    async def get_alarms():
        try:
            alarms_json_data = functions.read_json_data(alarms_json_file)
            alarms = alarms_json_data
            return JSONResponse(content=alarms)
        except Exception as e:
            logging.exception(f'Error on get alarms data function : {e.args[0]}')

    @staticmethod
    async def get_host_alarm():
        try:
            alarms_json_data = functions.read_json_data(alarms_json_file)
            host_alarms = alarms_json_data["ping-alarm"]
            return JSONResponse(content=host_alarms)
        except Exception as e:
            logging.exception(f'Error on get host alarms data function : {e.args[0]}')

    @staticmethod
    async def get_players_alarm():
        try:
            alarms_json_data = functions.read_json_data(alarms_json_file)
            players_alarms = alarms_json_data["players-alarms"]
            return JSONResponse(content=players_alarms)
        except Exception as e:
            logging.exception(f'Error on get players alarms data function : {e.args[0]}')

    @staticmethod
    async def get_analysis_file():
        return FileResponse('/appspace/appspace_players/databases/analysis.db', filename='appspace analysis.db')

    @staticmethod
    async def delete_analysis_file():
        try:
            connection = analysis_database.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT tbl_name from sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")
            connection.commit()
            connection.close()
            logging.info(f'Analysis file deleted successfully')
            return JSONResponse(content={'message': 'Analysis file deleted successfully'})
        except Exception as e:
            logging.exception(f'Error on delete analysis file function : {e.args[0]}')
