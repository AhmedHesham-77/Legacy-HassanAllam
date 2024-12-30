from shared.Classes.Database import DatabaseFunctions
from shared.Classes.Functions import SpecialFunctions
from starlette.responses import JSONResponse
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import logging
import json
import os

# Logging configuration
log_dir = '/entertainment/Entertainment_PCs/logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file_path = '/entertainment/Entertainment_PCs/logs/restapi.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a')
    ]
)

# Configration
database = DatabaseFunctions('/entertainment/Entertainment_PCs/databases/ChildrenMuseum.db')
functions = SpecialFunctions()
logger = logging.getLogger()
csv_path = '/entertainment/Entertainment_PCs/shared/csv/Entertainment PCs.csv'
table = 'EntertainmentPCs'
json_alarms_path = '/entertainment/Entertainment_PCs/json/EntertainmentPCs alarms.json'
analysis_database_path = '/entertainment/Entertainment_PCs/databases/analysis.db'
analysis_database = DatabaseFunctions(analysis_database_path)

try:
    locations = set({})
    for idx in functions.read_csv_data(csv_path):
        locations.add(idx[3])
except Exception as e:
    logger.exception(f"Error while getting locations from table {table}: {e.args[0]}")


class REST:
    def __init__(self):
        self.app = FastAPI()
        self.app.add_api_route("/devices", self.get_data, methods=["GET"])
        self.app.add_api_route("/devices/location={location}", self.get_location_data, methods=["GET"])
        self.app.add_api_route("/devices/location={location}/service={service}", self.get_service_data,
                               methods=["GET"])
        self.app.add_api_route("/devices/ips", self.get_ips, methods=["GET"])
        self.app.add_api_route("/alarms", self.get_alarms, methods=["GET"])
        self.app.add_api_route("/analysis-file", self.get_analysis_file, methods=["GET"])
        self.app.add_api_route("/delete/analysis-file", self.delete_analysis_file, methods=["DELETE"])

    @staticmethod
    async def get_location_data(location: str):
        location_response = {}
        names = set({})
        try:
            location_query = database.select_data_with_filter(table, {'location': location})
            for i in location_query:
                names.add(i[1])

            for name in names:
                name = name.lower()
                location_response[name] = {}
                for i in location_query:
                    if i[1].lower() == name:
                        if name not in location_response:
                            location_response[name] = {}
                        location_response[name][i[0]] = {'type': i[2], 'status': i[4]}

            logger.info(f"Data for {location} successfully retrieved")
            return JSONResponse(content=location_response)
        except Exception as exp:
            logger.exception(f"Error while getting data for location {location}: {exp.args[0]}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(exp.args[0])}")

    async def get_data(self):
        try:
            data_json = {}
            for location in locations:
                try:
                    location = location.lower()
                    location_response = await self.get_location_data(location)
                    data_json[location] = json.loads(location_response.body.decode('utf-8'))
                except Exception as exp:
                    logger.exception(f"Error while getting data for {location}: {str(exp.args[0])}")
                    data_json[location] = {"error": str(exp.args[0])}
            logger.info(f"Data for valid Locations retrieved successfully")
            return JSONResponse(content=data_json)
        except Exception as exp:
            logger.exception(f"Error while getting data: {exp.args[0]}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(exp.args[0])}")

    @staticmethod
    async def get_service_data(location: str, service: str):
        try:
            service_query = database.select_data_with_filter(table, {'location': location, 'name': service})
            service_response = {}
            for i in service_query:
                if i[1] not in service_response:
                    service_response[i[1]] = {}
                service_response[i[1]][i[0]] = {'type': i[2], 'status': i[4]}
            logger.info(f"Data for {location} and service {service} successfully retrieved")
            return JSONResponse(content=service_response)
        except Exception as exp:
            logger.exception(f"Error while getting data for location {location} and service {service}: {exp.args[0]}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(exp.args[0])}")

    @staticmethod
    async def get_ips():
        ips = {'ips': [ip[0] for ip in functions.read_csv_data(csv_path)]}
        logger.info(f"IPs data retrieved successfully")
        return JSONResponse(content=ips)

    @staticmethod
    async def get_alarms():
        try:
            alarms = functions.read_json_data(json_alarms_path)
            alarms = alarms.get('pc-ping', {})
            logger.info(f"Ping alarms data retrieved successfully")
            return JSONResponse(content=alarms)
        except Exception as e:
            logger.exception(f"Error while getting ping alarms data: {e.args[0]}")
            raise HTTPException(status_code=500, detail=f"Error while getting ping alarms data: {e.args[0]}")

    @staticmethod
    async def get_analysis_file():
        return FileResponse('/entertainment/Entertainment_PCs/databases/analysis.db', filename='entertain analysis.db')

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
