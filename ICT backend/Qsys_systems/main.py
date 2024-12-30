from shared.Classes.Database import DatabaseFunctions
from shared.Classes.Functions import SpecialFunctions
from logging import getLogger, basicConfig, INFO, FileHandler
from concurrent.futures import ThreadPoolExecutor
from shared.Classes.kong import Kong
from REST_API import REST
import schedule as sch
import pandas as pd
import requests
import datetime
import json
import time
import os

# log configration
log_file_path = '/Qsys/Qsys_systems/logs/main.log'
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
system_database_path = '/Qsys/Qsys_systems/databases/Qsys_systems.db'
analysis_database_path = '/Qsys/Qsys_systems/databases/analysis.db'
system_database = DatabaseFunctions(system_database_path)
analysis_database = DatabaseFunctions(analysis_database_path)
logger = getLogger()
json_alarm_path = '/Qsys/Qsys_systems/json/Qsys alarms.json'
csv_path = '/Qsys/Qsys_systems/shared/csv/Qsys IPs.csv'
ips_csv_res = functions.read_csv_data(csv_path)
ip_status = {ip[0]: ip[1] for ip in ips_csv_res}
ips_list = [ip[0] for ip in ips_csv_res]
ping_table = 'QsysPing'
data_table = 'QsysData'
rest = REST()
server_host = os.getenv('GLOBAL_SERVER_HOST')
server_port = int(os.getenv('QSYS_SERVER_PORT'))
skipped_types = ['Loudspeaker', 'Audio Video I/O']
devices_alarms_name = "device-alarms"
ping_alarms_name = "pc-ping"
analysis_table_name = 'QsysAnalysis'
kong = Kong(f'http://{os.getenv("GLOBAL_HOST")}:8001')


def ips_ping():
    try:
        ping_res = functions.ping_multiple_ips(ips_list)
    except Exception as e:
        logger.exception(f"Error while pinging IPs: {e.args[0]}")
        ping_res = {}

    try:
        system_database.create_table(ping_table, {'IP': 'TEXT', 'STATUS': 'TEXT', 'PING_RESULT': 'TEXT'}, 'IP')
        for ip, value in ping_res.items():
            data = functions.read_json_data(json_alarm_path)
            if ping_alarms_name in data and ip in data[ping_alarms_name]:
                del data[ping_alarms_name][ip]
                with open(json_alarm_path, 'w') as json_file:
                    json.dump(data, json_file, indent=4)

            if value == 'OFF':
                dic = {f'{ip}': f"Ip is down with status {value}"}
                SpecialFunctions.update_json_data(json_alarm_path, dic, "pc-ping")

            check_query = system_database.select_data_with_filter(ping_table, {'IP': ip})

            try:
                if check_query:
                    system_database.update_table(ping_table, {'STATUS': ip_status[ip], 'PING_RESULT': value},
                                                 {'IP': ip})
                else:
                    system_database.insert_in_table(ping_table, [ip, ip_status[ip], value])
            except Exception as e:
                logger.exception(f"Error with table {ping_table}: {e.args[0]}")

        logger.info("IPs pinged successfully")
    except Exception as e:
        logger.exception(f"Error with table {ping_table}: {e.args[0]}")


def main():
    logger.info('Main function started')
    data_ip = None
    try:
        data = pd.DataFrame(system_database.select_data(ping_table))
        data['sort_key'] = data[0].str.extract(r'\.(\d+)$').astype(int)
        data_ip = data.sort_values(by='sort_key').drop(columns=['sort_key']).head(1)[0].values[0]
        logger.info(f"Data IP: {data_ip}")
    except Exception as e:
        logger.exception(f"Error while getting data IP: {e.args[0]}")

    if data_ip is not None:
        body = {
            "username": os.getenv('QSYS_USERNAME'),
            "password": os.getenv('QSYS_PASSWORD')
        }

        login = requests.post(f'http://{data_ip}/api/v0/logon', json=body, headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        token = login.json()['token']

        speakers_data = requests.get(f'http://{data_ip}/api/v0/systems/1/items', headers={
            "Accept": "application/json",
            "Authorization": f'Bearer {token}'
        }).json()

        system_database.create_table(data_table, {
            'ID': 'INTEGER', 'NAME': 'TEXT', 'TYPE': 'TEXT', 'LOCATION': 'TEXT', 'IS_REDUNDANT': 'TEXT',
            'PRIMARY_ACTIVE': 'TEXT', 'PRIMARY_NAME': 'TEXT', 'BACKUP_ACTIVE': 'TEXT', 'BACKUP_NAME': 'TEXT',
            'SERIAL_NUMBER': 'TEXT', 'FIRMWARE_VERSION': 'TEXT', 'LAN_A_MODE': 'TEXT', 'LAN_A_LINK': 'TEXT',
            'LAN_A_IP': 'TEXT', 'LAN_B_MODE': 'TEXT', 'LAN_B_LINK': 'TEXT', 'LAN_B_IP': 'TEXT',
            'STATUS_CODE': 'INTEGER', 'STATUS_MESSAGE': 'TEXT', 'STATUS_DETAILS': 'TEXT'
        }, 'ID')

        try:
            # Ensure network_interfaces is not None
            for speaker in speakers_data:
                if speaker['type'] in skipped_types:
                    continue

                json_data = functions.read_json_data(json_alarm_path)
                if devices_alarms_name in json_data and speaker['id'] in json_data[devices_alarms_name]:
                    del json_data[devices_alarms_name][speaker['id']]
                    with open(json_alarm_path, 'w') as json_file:
                        json.dump(json_data, json_file, indent=4)

                if speaker['status']['code'] != 0:
                    dic = {
                        f'{speaker["id"]}': f"{speaker['type']} is down with status code {speaker['status']['code']}"
                                            f" and message {speaker['status']['message']} "
                                            f"and details {speaker['status']['details']}"}
                    SpecialFunctions.update_json_data(json_alarm_path, dic, devices_alarms_name)

                try:
                    network_interfaces = speaker['assetInfo'].get('networkInterfaces', [])
                    if network_interfaces is None:
                        network_interfaces = []
                    lan_a_mode = network_interfaces[0].get('Mode', 'null') if len(network_interfaces) > 0 else 'null'
                    lan_a_link = network_interfaces[0].get('Link', 'null') if len(network_interfaces) > 0 else 'null'
                    lan_a_ip = network_interfaces[0].get('IP', 'null') if len(network_interfaces) > 0 else 'null'
                    lan_b_mode = network_interfaces[1].get('Mode', 'null') if len(network_interfaces) > 1 else 'null'
                    lan_b_link = network_interfaces[1].get('Link', 'null') if len(network_interfaces) > 1 else 'null'
                    lan_b_ip = network_interfaces[1].get('IP', 'null') if len(network_interfaces) > 1 else 'null'
                except (AttributeError, IndexError):
                    lan_a_mode = lan_a_link = lan_a_ip = lan_b_mode = lan_b_link = lan_b_ip = 'null'
                try:
                    check_query = system_database.select_data_with_filter(data_table, {'ID': speaker['id']})

                    if check_query:
                        system_database.update_table(data_table,
                                                     {'NAME': speaker['name'].lower(), 'TYPE': speaker['type'],
                                                      'LOCATION': speaker['location'].lower(),
                                                      'IS_REDUNDANT': speaker['redundancy']['isRedundant'],
                                                      'PRIMARY_ACTIVE': speaker['redundancy']['primaryActive'],
                                                      'PRIMARY_NAME': speaker['redundancy']['primaryName'],
                                                      'BACKUP_ACTIVE': speaker['redundancy']['backupActive'],
                                                      'BACKUP_NAME': speaker['redundancy']['backupName'],
                                                      'SERIAL_NUMBER': speaker['assetInfo']['serialNumber'],
                                                      'FIRMWARE_VERSION': speaker['assetInfo']['firmwareVersion'],
                                                      'LAN_A_MODE': lan_a_mode, 'LAN_A_LINK': lan_a_link,
                                                      'LAN_A_IP': lan_a_ip, 'LAN_B_MODE': lan_b_mode,
                                                      'LAN_B_LINK': lan_b_link,
                                                      'LAN_B_IP': lan_b_ip,
                                                      'STATUS_CODE': speaker['status']['code'],
                                                      'STATUS_MESSAGE': speaker['status']['message'],
                                                      'STATUS_DETAILS': speaker['status']['details']},
                                                     {'ID': speaker['id']})
                    else:
                        system_database.insert_in_table(data_table, [
                            speaker['id'], speaker['name'].lower(), speaker['type'], speaker['location'].lower(),
                            speaker['redundancy']['isRedundant'], speaker['redundancy']['primaryActive'],
                            speaker['redundancy']['primaryName'], speaker['redundancy']['backupActive'],
                            speaker['redundancy']['backupName'], speaker['assetInfo']['serialNumber'],
                            speaker['assetInfo']['firmwareVersion'], lan_a_mode, lan_a_link, lan_a_ip,
                            lan_b_mode, lan_b_link, lan_b_ip, speaker['status']['code'],
                            speaker['status']['message'], speaker['status']['details']
                        ])
                except Exception as e:
                    logger.exception(f"Error while updating table {data_table}: {e.args[0]}")
            logger.info(f"Table {data_table} updated successfully")
        except Exception as e:
            logger.exception(f"Error while updating table {data_table}: {e.args[0]}")

        try:
            services = kong.get_services()
            service_id = ''
            route_added = False
            for service in services['data']:
                if service['name'] == 'qsys':
                    service_id = service['id']
                    break
            if service_id == '':
                new_service = kong.add_service('qsys', f'http://{os.getenv("GLOBAL_HOST")}:{server_port}')
                service_id = new_service['id']
                logger.info('Service added successfully')

            routes = kong.get_routes()
            for route in routes['data']:
                if route['name'] == 'qsys':
                    route_added = True
                    break
            if not route_added:
                kong.add_route(service_id, 'qsys','/qsys')
                logger.info('Route added successfully')
        except Exception as exp:
            logger.exception(f"Error while adding service: {exp.args}")
    else:
        logger.error("Data IP is None")


def fill_analysis_table():
    try:
        analysis_database.create_table(analysis_table_name, {
            'ID': 'INTEGER', 'NAME': 'TEXT', 'TYPE': 'TEXT', 'LOCATION': 'TEXT', 'IS_REDUNDANT': 'TEXT',
            'PRIMARY_ACTIVE': 'TEXT', 'PRIMARY_NAME': 'TEXT', 'BACKUP_ACTIVE': 'TEXT', 'BACKUP_NAME': 'TEXT',
            'SERIAL_NUMBER': 'TEXT', 'FIRMWARE_VERSION': 'TEXT', 'LAN_A_MODE': 'TEXT', 'LAN_A_LINK': 'TEXT',
            'LAN_A_IP': 'TEXT', 'LAN_B_MODE': 'TEXT', 'LAN_B_LINK': 'TEXT', 'LAN_B_IP': 'TEXT',
            'STATUS_CODE': 'INTEGER', 'STATUS_MESSAGE': 'TEXT', 'STATUS_DETAILS': 'TEXT', 'DATE_TIME': 'TIMESTAMP'
        }, 'ID, DATE_TIME')

        data = system_database.select_data(data_table)
        for row in data:
            row = list(row)
            row.append(datetime.datetime.now())
            analysis_database.insert_in_table(analysis_table_name, row)
        logger.info(f"Table {analysis_table_name} filled successfully")
    except Exception as e:
        logger.exception(f"Error while filling analysis table : {e.args[0]}")
    logger.info('Analysis function executed successfully')


def run_program():
    try:
        ips_ping()
    except Exception as exp:
        logger.exception(f"Error while pinging IPs: {exp.args[0]}")
    while True:
        sch.run_pending()
        time.sleep(1)


sch.every().hour.do(fill_analysis_table)
sch.every(5).seconds.do(ips_ping)
sch.every(30).seconds.do(main)

if __name__ == "__main__":
    with ThreadPoolExecutor() as executor:
        executor.submit(run_program)
        executor.submit(functions.run_server(rest.app, server_host, server_port, logger))
