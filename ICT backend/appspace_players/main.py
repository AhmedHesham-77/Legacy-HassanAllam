from appspace_requests import AppspaceRequests
from shared.Classes.Functions import SpecialFunctions
from shared.Classes.Database import DatabaseFunctions
from shared.Classes.kong import Kong
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as eT
from REST_API import REST
import schedule as sch
import datetime
import logging
import time
import json
import os
import re

# Logging configuration
log_file_path = '/appspace/appspace_players/logs/main.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a')
    ]
)

# Configration
rest = REST()
appspace_requests = AppspaceRequests()
functions = SpecialFunctions()
appspace_host_status = {}
kong = Kong(f'http://{os.getenv("GLOBAL_HOST")}:8001')
server_host = os.getenv('GLOBAL_SERVER_HOST')
server_port = int(os.getenv('APPSPACE_SERVER_PORT'))
appspace_host = os.getenv('APPSPACE_HOST')
json_alarm_path = '/appspace/appspace_players/json/alarms.json'
json_players_path = '/appspace/appspace_players/json/players.json'
devices_database_path = '/appspace/appspace_players/databases/devices.db'
analysis_database_path = '/appspace/appspace_players/databases/analysis.db'
ping_alarm_var = 'ping-alarm'
players_alarms_var = 'players-alarms'
devices_database = DatabaseFunctions(devices_database_path)
analysis_database = DatabaseFunctions(analysis_database_path)
group_data = {}


def find_id(group, target, keys, parents=None):
    if parents is None:
        parents = []
    for item in group:
        if item[keys['id']] == target:
            if item[keys['parent']] > 0:
                return find_id(group, item[keys['parent']], keys, parents + [str(item[keys['id']])])
            else:
                return parents + [str(item[keys['id']])]
    return None


def ping_host():
    functions.ping(appspace_host, appspace_host_status)

    json_data = functions.read_json_data(json_alarm_path)
    if ping_alarm_var not in json_data:
        alarm = {
            f"{ping_alarm_var}": {}
        }
        functions.update_json_data(json_alarm_path, alarm)

    if appspace_host_status[appspace_host] == 'OFF':
        logging.info(f'Appspace host is down')
        alarm = {
            f"{appspace_host}": "Appspace host is down"
        }
        functions.update_json_data(json_alarm_path, alarm, ping_alarm_var)

    else:
        logging.info(f'Appspace host is up')
        json_data = functions.read_json_data(json_alarm_path)
        if ping_alarm_var in json_data and appspace_host in json_data[ping_alarm_var]:
            del json_data[ping_alarm_var][appspace_host]
            with open(json_alarm_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)


def main():
    paths = {}
    ping_host()
    json_data = functions.read_json_data(json_alarm_path)
    if json_data[ping_alarm_var] == {}:
        try:
            appspace_access_token = appspace_requests.get_token()
            try:
                root = eT.fromstring(appspace_access_token.text)
                namespace = {
                    'ns': 'http://schemas.datacontract.org/2004/07/Nexus.AppSpace.Service.Contract.Messages.Token'}
                security_token = root.find('.//ns:SecurityToken', namespace)
                logging.info(f"Token received successfully with status code: {appspace_access_token.status_code}")
                appspace_requests.get_headers.update({'token': security_token.text})
            except Exception as e:
                logging.exception(
                    f"Error while getting token with status code {appspace_access_token.status_code}, \n {e.args[0]}")
                return

        except Exception as e:
            logging.exception(f"Error while getting token: {e.args[0]}")
            return

        try:
            groups = appspace_requests.get_groups_data()
            new_data = {}

            for group in groups:
                group_name = group['Name']
                group_id = group['Id']
                parent_id = group['ParentId']
                group_data[group_id] = group_name

                if parent_id > 0:
                    parent_path = find_id(groups, parent_id, keys={'id': 'Id', 'parent': 'ParentId'})
                    if parent_path is not None:
                        split_path = re.findall(r"\['\d+'\]", str(parent_path))
                        looping_path = 'new_data'
                        for idx in split_path:
                            if idx[1:-1] not in looping_path:
                                looping_path += idx
                                try:
                                    eval(f'{looping_path}')
                                except:
                                    exec(f'{looping_path} = {{}}')
                        old_value = eval(f'{looping_path}')
                        old_value.update({group_id: {"name": group_name}})
                        exec(f'{looping_path} = old_value')
                        paths[group_id] = f'{parent_path}' + f'{[str(group_id)]}'
                else:
                    if f'\'{group_id}\'' in new_data:
                        new_data[str(group_id)].update({"name": group_name})
                    else:
                        new_data[str(group_id)] = {"name": group_name}
                        paths[group_id] = f'[\'{group_id}\']'
            functions.write_json_data(json_players_path, new_data)
            logging.info("Players groups updated successfully")
        except Exception as e:
            logging.exception(f"Error while getting groups data: {e.args[0]}")
            return

        try:
            devices_data = appspace_requests.get_devices_data()
            players_json_data = functions.read_json_data(json_players_path)
            devices_database.create_table('devices',
                                          {'id': 'TEXT', 'name': 'TEXT', 'groupId': 'TEXT', 'groupName': 'TEXT',
                                           'ip': 'TEXT',
                                           'status': 'TEXT'},
                                          'id')
            for device in devices_data:
                player_group = device['PlayerGroupId']
                device_data = {device['Id']: {
                    "name": device['Name'],
                    "ip": device['IP'],
                    "status": device['Status'],
                }}
                device_group_data = eval('players_json_data' + str(paths[player_group]))
                if 'devices' in device_group_data:
                    eval('players_json_data' + str(paths[player_group]))['devices'].update(device_data)
                else:
                    eval('players_json_data' + str(paths[player_group]))['devices'] = device_data

                try:
                    check = devices_database.select_data_with_filter('devices', {'id': device['Id']})
                    if check:
                        devices_database.update_table('devices', {'name': device['Name'], 'groupId': player_group,
                                                                  'groupName': group_data[player_group],
                                                                  'ip': device['IP'], 'status': device['Status']},
                                                      {'id': device['Id']})
                    else:
                        devices_database.insert_in_table('devices', [device['Id'], device['Name'], player_group,
                                                                     group_data[player_group], device['IP'],
                                                                     device['Status']])
                except Exception as e:
                    logging.exception(f"Error while updating devices data: {e.args[0]}")

                alarm = {}
                if device['Status'] == 1:
                    alarm = {
                        f"{device['Id']}": f"Device {device['Name']} with IP {device['IP']} is offline"
                    }
                elif device['Status'] == 3:
                    alarm = {
                        f"{device['Id']}": f"Lost communication with device {device['Name']} with IP {device['IP']}"
                    }
                if alarm != {}:
                    functions.update_json_data(json_alarm_path, alarm, players_alarms_var)

            functions.write_json_data(json_players_path, players_json_data)
            logging.info("Players data updated successfully")
        except Exception as e:
            logging.exception(f"Error while getting devices data: {e.args[0]}")
            return

        try:
            services = kong.get_services()
            service_id = ''
            route_added = False
            for service in services['data']:
                if service['name'] == 'appspace':
                    service_id = service['id']
                    break
            if service_id == '':
                new_service = kong.add_service('appspace', f'http://{os.getenv("GLOBAL_HOST")}:{server_port}')
                service_id = new_service['id']
                logging.info('Service added successfully')

            routes = kong.get_routes()
            for route in routes['data']:
                if route['name'] == 'appspace':
                    route_added = True
                    break
            if not route_added:
                kong.add_route(service_id, 'appspace','/appspace')
                logging.info('Route added successfully')
        except Exception as exp:
            logging.exception(f"Error while adding service: {exp.args}")


def fill_analysis_database():
    try:
        devices_data = list(devices_database.select_data('devices'))
        analysis_database.create_table('analysis',
                                       {'id': 'TEXT', 'name': 'TEXT', 'groupId': 'TEXT', 'groupName': 'TEXT',
                                        'ip': 'TEXT',
                                        'status': 'TEXT', 'time': 'TIMESTAMP'}, 'id, time')
        for device in devices_data:
            device = list(device)
            device.append(datetime.datetime.now())
            analysis_database.insert_in_table('analysis', device)
        logging.info("Analysis database filled successfully")
    except Exception as e:
        logging.exception(f"Error while filling analysis database: {e.args[0]}")


def run_schedules():
    try:
        ping_host()
    except Exception as e:
        logging.exception(f"Error while running ping_host function: {e.args[0]}")
    while True:
        sch.run_pending()
        time.sleep(1)


# Set schedules
sch.every().minute.do(main)
sch.every().hour.do(fill_analysis_database)
sch.every(5).seconds.do(ping_host)

if __name__ == '__main__':
    with ThreadPoolExecutor() as executor:
        executor.submit(run_schedules)
        executor.submit(functions.run_server(rest.app, server_host, server_port, logging))
