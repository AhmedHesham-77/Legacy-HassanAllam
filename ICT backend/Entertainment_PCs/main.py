import time
from shared.Classes.kong import Kong
from shared.Classes.Functions import SpecialFunctions
from shared.Classes.Database import DatabaseFunctions
from concurrent.futures import ThreadPoolExecutor
from REST_API import REST
import schedule as sch
import datetime
import logging
import json
import os

# Logging configuration
log_dir = '/entertainment/Entertainment_PCs/logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file_path = '/entertainment/Entertainment_PCs/logs/main.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a')
    ]
)

# Configurations
rest = REST()
functions = SpecialFunctions()
analysis_database_path = '/entertainment/Entertainment_PCs/databases/analysis.db'
system_database_path = '/entertainment/Entertainment_PCs/databases/ChildrenMuseum.db'
csv_path = '/entertainment/Entertainment_PCs/shared/csv/Entertainment PCs.csv'
json_path = '/entertainment/Entertainment_PCs/json/EntertainmentPCs alarms.json'
system_database = DatabaseFunctions(system_database_path)
analysis_database = DatabaseFunctions(analysis_database_path)
csv_data = functions.read_csv_data(csv_path)
data = {row[0]: row[1:] for row in csv_data}
ips = data.keys()
server_host = os.getenv('GLOBAL_SERVER_HOST')
server_port = int(os.getenv('ENTERTAINMENT_SERVER_PORT'))
logger = logging.getLogger()
table_name = 'EntertainmentPCs'
ping_alarm_name = 'ping-alarms'
kong = Kong(f'http://{os.getenv("GLOBAL_HOST")}:8001')


def main():
    system_database.create_table('EntertainmentPCs',
                                 {'ip': 'TEXT', 'name': 'TEXT', 'type': 'TEXT',
                                  'location': 'TEXT', 'status': 'TEXT'},
                                 'ip')
    ping_result = {}
    try:
        ping_result = functions.ping_multiple_ips(ips)
    except Exception as exp:
        logger.exception(f"Error while ping on ips as {exp.args[0]}")

    try:
        for ip in ping_result:
            check_query = f"""
             SELECT COUNT(*) FROM "{table_name}"
             where ip = ?;
            """

            json_data = functions.read_json_data(json_path)
            if ping_alarm_name in json_data and ip in json_data[ping_alarm_name]:
                del json_data[ping_alarm_name][ip]
                with open(json_path, 'w') as json_file:
                    json.dump(json_data, json_file, indent=4)

            if ping_result[ip] == 'OFF':
                dic = {f'{ip}': f"PC with this ip is down with status {ping_result[ip]}"}
                functions.update_json_data(json_path, dic, ping_alarm_name)

            if not isinstance(check_query, str):
                check_query = str(check_query)
            conn = system_database.get_connection()
            cursor = conn.cursor()
            cursor.execute(check_query, (ip,))
            count = cursor.fetchone()[0]

            if count:
                system_database.update_table('EntertainmentPCs',
                                             {'name': data[ip][0].lower(), 'type': data[ip][1],
                                              'location': data[ip][2].lower(), 'status': ping_result[ip]},
                                             {'ip': ip})
            else:
                insert_data = [ip, data[ip][0].lower(), data[ip][1], data[ip][2].lower(), ping_result[ip]]
                system_database.insert_in_table('EntertainmentPCs', insert_data)
        logger.info(f"Table {table_name} updated successfully")
    except Exception as exp:
        logger.exception(f"Error while update table {table_name} as {exp.args[0]}")

    try:
        services = kong.get_services()
        service_id = ''
        route_added = False
        for service in services['data']:
            if service['name'] == 'entertainment':
                service_id = service['id']
                break
        if service_id == '':
            new_service = kong.add_service('entertainment', f'http://{os.getenv("GLOBAL_HOST")}:{server_port}')
            service_id = new_service['id']
            logger.info('Service added successfully')

        routes = kong.get_routes()
        for route in routes['data']:
            if route['name'] == 'entertainment':
                route_added = True
                break
        if not route_added:
            kong.add_route(service_id, 'entertainment', '/entertainment')
            logger.info('Route added successfully')

    except Exception as exp:
        logger.exception(f"Error while adding service: {exp.args}")


def fill_analysis():
    try:
        pcs_data = system_database.select_data(table_name)
        analysis_database.create_table(table_name, {'ip': 'TEXT', 'name': 'TEXT', 'type': 'TEXT', 'location': 'TEXT',
                                                    'status': 'TEXT', 'date_time': 'TIMESTAMP'}, 'ip, date_time')
        for pc in pcs_data:
            row = list(pc)
            row.append(datetime.datetime.now())
            analysis_database.insert_in_table(table_name, row)
    except Exception as e:
        logger.exception(f"Error while fetching data from {table_name} as {e.args[0]}")
    logger.info('Analysis function executed successfully')


def run_program():
    while True:
        sch.run_pending()
        time.sleep(1)


# Set schedules
sch.every().hour.do(fill_analysis)
sch.every().minute.do(main)

if __name__ == '__main__':
    with ThreadPoolExecutor() as executor:
        executor.submit(run_program)
        executor.submit(functions.run_server(rest.app, server_host, server_port, logger))
