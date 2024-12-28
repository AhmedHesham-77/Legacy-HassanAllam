from fastapi import FastAPI, HTTPException, Request, responses
from Classes.Functions import SpecialFunctions
from Classes.Database import DatabaseFunctions
from starlette.responses import JSONResponse
from Classes.SNMP import SNMPFunctions
from collections import defaultdict
import pandas as pd
import logging
import json
import os

# Logging configuration
log_file_path = 'logs/restapi.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a')
    ]
)

# Configration
database = DatabaseFunctions('databases/fida.db')
location_list = defaultdict(list)
functions = SpecialFunctions()
logger = logging.getLogger()
snmp = SNMPFunctions()
ips_csv_path = 'csv/IPs.csv'
fida_working_table = 'working_fida'
json_alarms_path = 'json/alarms.json'
community = 'public'

try:
    for row in functions.read_csv_data(ips_csv_path):
        location_list[row[1]].append(row[0])
except Exception as e:
    logger.exception(f"Error while reading {ips_csv_path} : {str(e.args[0])}")


class REST:
    def __init__(self):
        self.app = FastAPI()
        self.app.add_api_route("/fida/data", self.get_data, methods=["GET"])
        self.app.add_api_route("/fida/data/location={location}", self.get_data_for_location, methods=["GET"])
        self.app.add_api_route("/fida/data/ips", self.get_ips, methods=["GET"])
        self.app.add_api_route("/fida/schedule", self.set_schedule, methods=["PUT"])
        self.app.add_api_route("/fida/schedule/ip={ip}", self.set_schedule_for_ip, methods=["PUT"])
        self.app.add_api_route("/fida/alarms", self.get_alarms, methods=["GET"])
        self.app.add_api_route("/fida/alarms/ping", self.get_ping_alarms, methods=["GET"])
        self.ips_data = [ip for ips in location_list.values() for ip in ips]

    @staticmethod
    async def get_data_for_location(location: str):
        """GET request to get JSON for {ip}"""
        try:
            result = {}
            for ip in location_list[location.lower()]:
                result[ip] = {}
                check_ping = database.select_data_with_filter(fida_working_table, {'ip': ip})

                if not check_ping or check_ping[0][1] != 'ON':
                    result[ip] = {"error": "IP status is not ON or no result found"}
                    continue

                connection = database.get_connection()
                cursor = connection.cursor()
                cursor.execute(f"SELECT status FROM working_pcs WHERE fida_ip = '{ip}'")
                pc_status = cursor.fetchone()
                result[ip] = {'pc_status': pc_status[0]}
                table_name = f"fida_{ip[ip.rfind('.') + 1:]}"
                query = database.select_data(table_name)

                for data in query:
                    oid = data[0]
                    name = data[1]
                    value = data[2]
                    result[ip][name] = {'oid': oid, 'value': value}

            logger.info(f"Data for {location} successfully retrieved")
            return JSONResponse(content=result)
        except Exception as exp:
            logger.exception(f"Error while getting data for {location}: {str(exp.args[0])}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(exp.args[0])}")

    async def get_data(self):
        """GET request to get JSON for all IPs"""
        try:
            all_data_json = {}
            for location in location_list:
                try:
                    data = await self.get_data_for_location(location)
                    all_data_json[f'{location}'] = json.loads(data.body.decode('utf-8'))
                except Exception as exp:
                    logger.exception(f"Error while getting data for {location}: {str(exp.args[0])}")
                    all_data_json[f'{location}'] = {"error": str(exp.args[0])}
            logger.info(f"Data for valid Locations retrieved successfully")
            return JSONResponse(content=all_data_json)
        except Exception as exp:
            logger.exception(f"Error while getting data for all IPs: {str(exp.args[0])}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(exp.args[0])}")

    async def get_ips(self):
        ips = {'ips': self.ips_data}
        return responses.JSONResponse(content=ips)

    @staticmethod
    async def set_schedule_for_ip(ip: str, request: Request):
        """PUT request to set IP new schedule"""
        args = await request.json()
        for i in args:
            try:
                table_name = f"fida_{ip[ip.rfind('.') + 1:]}"
                query = database.select_data_with_filter(table_name, {'name': i})
                if not query:
                    logger.exception(f"(function: set_schedule_for_ip) : Data not found for {i}")
                    raise HTTPException(status_code=404, detail=f"Data not found for {i}")
                oid = query[0][0]
                new_val = int(float(args[i]) * 60)
                database.update_table(table_name, {'value': new_val}, {'oid': oid})
                snmp.set_value_on_ip(ip, oid, community, str(new_val))
                logger.info(f"Schedule for {ip} updated successfully")
            except Exception as exp:
                logger.exception(f"Error while setting schedule for {ip}: {str(exp.args[0])}")
                raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(exp.args[0])}")
        return responses.JSONResponse(content={'message': f'Schedule for {ip} up to date'})

    async def set_schedule(self, request: Request):
        """PUT request to set all IPs to schedule"""
        try:
            working_ips = database.select_data(fida_working_table)
            ips = [ip[0] for ip in working_ips if ip[1] == 'ON']
            for ip in ips:
                await self.set_schedule_for_ip(ip, request)
            logger.info(f"Schedule for all IPs up to date")
            return responses.JSONResponse(content={'message': f'Schedule for all IPs up to date'})
        except Exception as exp:
            logger.exception(f"Error while setting schedule for all IPs: {str(exp.args[0])}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(exp.args[0])}")

    @staticmethod
    async def get_alarms():
        try:
            alarms = functions.read_json_data(json_alarms_path)
        except FileNotFoundError:
            alarms = {}
        except json.JSONDecodeError:
            alarms = {}
        except Exception as exp:
            logger.exception(f"Error while getting alarms: {str(exp.args[0])}")
            alarms = {"error": str(exp.args[0])}
        return alarms

    @staticmethod
    async def get_ping_alarms():
        try:
            json_data = functions.read_json_data(json_alarms_path)
            alarms = json_data['ping']
        except FileNotFoundError:
            alarms = {}
        except json.JSONDecodeError:
            alarms = {}
        except Exception as exp:
            logger.exception(f"Error while getting ping alarms: {str(exp.args[0])}")
            alarms = {"error": str(exp.args[0])}
        return alarms

    def update(self):
        self.ips_data = pd.read_csv('csv/IPs.csv')['IP'].tolist()
