import uvicorn
import multiprocessing as mp
from shared.Classes.Database import DatabaseFunctions
from ping3 import ping
import json
import csv
import os


class SpecialFunctions:

    def __init__(self):
        pass

    # Read data from a csv file
    @staticmethod
    def read_csv_data(path):
        try:
            with open(path, 'r') as file:
                data = csv.reader(file, delimiter=',')
                next(data)
                return list(data)
        except Exception as e:
            raise Exception(f'Error while reading csv file with path {path} : {e}')

    # Write data to a csv file
    @staticmethod
    def write_csv_data(path, data):
        try:
            with open(path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data)
        except Exception as e:
            raise Exception(f'Error while writing csv file with path {path} : {e}')

    # Append data to a csv file
    @staticmethod
    def append_csv_data(path, data):
        try:
            with open(path, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(data)
        except Exception as e:
            raise Exception(f'Error while updating csv file with path {path} : {e}')

    # Read data from a json file
    @staticmethod
    def read_json_data(path):
        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        if not os.path.exists(path):
            with open(path, 'w') as file:
                json.dump({}, file)
            return {}

        try:
            with open(path, 'r') as file:
                data = json.load(file)
                return data
        except json.JSONDecodeError:
            raise Exception(f"Error while reading json file: {path} contains invalid JSON. Returning empty dictionary.")
        except Exception as e:
            raise Exception(f"Error while reading json file with path {path}: {e}")

    # Write data to a json file
    @staticmethod
    def write_json_data(path, new_data):
        with open(path, 'w') as json_file:
            json.dump(new_data, json_file, indent=4)

    # Update json file with parameter and sub parameter
    @staticmethod
    def update_json_data(path, new_data, param=None, sub_param=None):
        if not os.path.exists(path):
            open(path, 'w').close()
        data = SpecialFunctions.read_json_data(path)
        if param:
            if param not in data or not isinstance(data[param], dict):
                data[param] = {}
            if sub_param:
                if sub_param not in data[param] or not isinstance(data[param][sub_param], dict):
                    data[param][sub_param] = {}
                data[param][sub_param].update(new_data)
            else:
                data[param].update(new_data)
        else:
            data.update(new_data)
        with open(path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    # Delete all files data
    @staticmethod
    def clear_file(path):
        open(f'{path}', 'w').close()

    # Ping a list of IPs
    @staticmethod
    def ping(ip, status):
        if ip:
            ping1, ping2, ping3 = ping(ip, timeout=2), ping(ip, timeout=2), ping(ip, timeout=2)
            if isinstance(ping1, float) and isinstance(ping2, float) and isinstance(ping3, float):
                status[ip] = 'ON'
            else:
                status[ip] = 'OFF'

    @staticmethod
    def ping_multiple_ips(ips_list):
        try:
            with mp.Manager() as manager:
                status = manager.dict()
                processes = []
                for ip in ips_list:
                    try:
                        process = mp.Process(target=SpecialFunctions.ping, args=(ip, status))
                        processes.append(process)
                        process.start()
                    except Exception as e:
                        raise Exception(f'Error while creating process for {ip}: {e}')
                try:
                    for process in processes:
                        process.join()
                except Exception as e:
                    raise Exception(f'Error while joining processes: {e}')
                return dict(status)
        except Exception as e:
            raise Exception(f'Error while pinging multiple IPs: {e}')

    @staticmethod
    def update_ping_tables(database_name, table_name, ping_result):
        database = DatabaseFunctions(database_name)
        down_ips = []
        try:
            for ip in ping_result:
                conn = database.get_connection()
                cursor = conn.cursor()
                count_query = f"""SELECT COUNT(*) FROM {table_name} WHERE ip = ?;"""
                cursor.execute(count_query, (ip,))
                count = cursor.fetchone()[0]
                if count > 0:
                    database.update_table(table_name, dict({'status': ping_result[ip]}), {'ip': ip})
                else:
                    database.insert_in_table(table_name, [ip, ping_result[ip]])
        except Exception as exp:
            raise Exception(f"Error while updating table {table_name}: {exp.args[0]}")
        return down_ips

    @staticmethod
    def run_server(app, server_host, server_port, logger):
        try:
            uvicorn.run(app, host=server_host, port=server_port)
            logger.info('Server started successfully')
        except Exception as exp:
            logger.exception(f"Error while running server: {exp.args[0]}")
