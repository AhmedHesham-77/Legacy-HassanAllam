from shared.Classes.Database import DatabaseFunctions
from shared.Classes.Functions import SpecialFunctions
from logging import getLogger, basicConfig, INFO, FileHandler
from starlette.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException
import json
import os

# log configration
log_file_path = '/Qsys/Qsys_systems/logs/rest_api.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
basicConfig(
    level=INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        FileHandler(log_file_path, mode='a')
    ]
)

# Configration
functions = SpecialFunctions()
database = DatabaseFunctions('/Qsys/Qsys_systems/databases/Qsys_systems.db')
logger = getLogger()
data_table_name = 'QsysData'
json_alarms_path = 'Qsys_systems/json/Qsys alarms.json'
analysis_database_path = '/Qsys/Qsys_systems/databases/analysis.db'
analysis_database = DatabaseFunctions(analysis_database_path)


class REST:
    def __init__(self):
        self.app = FastAPI()
        self.app.add_api_route('/devices', self.get_all_locations_data, methods=['GET'])
        self.app.add_api_route('/devices/location={location}', self.get_location_data, methods=['GET'])
        self.app.add_api_route('/alarms', self.get_alarms, methods=['GET'])
        self.app.add_api_route('/alarms/ping', self.get_ping_alarms, methods=['GET'])
        self.app.add_api_route("/analysis-file", self.get_analysis_file, methods=["GET"])
        self.app.add_api_route("/delete/analysis-file", self.delete_analysis_file, methods=["DELETE"])

    @staticmethod
    async def get_location_data(location: str):
        try:
            response = {}
            location = location.lower()
            data = database.select_data(data_table_name)
            columns_names = database.get_columns_names(data_table_name)
            location_data = [i for i in data if i[3] == location]
            types = set({})
            for i in location_data:
                types.add(i[2])

            for i in types:
                response[i] = [
                    ({col: j[idx] for idx, col in enumerate(columns_names[:2])} |
                     {col: j[idx] for idx, col in enumerate(columns_names[4:], start=4)})
                    for j in location_data if j[2] == i]

            logger.info(f"Data for location {location} successfully retrieved")
            return JSONResponse(content=response)
        except Exception as e:
            logger.exception(f"Error while getting data for location {location}: {e.args[0]}")
            raise HTTPException(status_code=500,
                                detail=f"Error while getting data for location {location}: {e.args[0]}")

    async def get_all_locations_data(self):
        try:
            response = {}
            data = database.select_data(data_table_name)
            locations = set({i[3] for i in data})

            for location in locations:
                try:
                    location = location.lower()
                    location_response = await self.get_location_data(location)
                    response[location] = json.loads(location_response.body.decode('utf-8'))
                except Exception as exp:
                    logger.exception(f"Error while getting data for {location}: {str(exp.args[0])}")
                    response[location] = {"error": str(exp.args[0])}
            logger.info(f"Data for valid Locations retrieved successfully")
            return JSONResponse(content=response)

        except Exception as e:
            logger.exception(f"Error while getting all locations data: {e.args[0]}")
            raise HTTPException(status_code=500, detail=f"Error while getting all locations data: {e.args[0]}")

    @staticmethod
    async def get_alarms():
        try:
            alarms = functions.read_json_data(json_alarms_path)
            logger.info(f"Alarms data retrieved successfully")
            return JSONResponse(content=alarms)
        except Exception as e:
            logger.exception(f"Error while getting alarms data: {e.args[0]}")
            raise HTTPException(status_code=500, detail=f"Error while getting alarms data: {e.args[0]}")

    @staticmethod
    async def get_ping_alarms():
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
        return FileResponse('/Qsys/Qsys_systems/databases/analysis.db', filename='qsys analysis.db')

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
