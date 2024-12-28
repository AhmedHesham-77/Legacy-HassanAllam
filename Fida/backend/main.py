from concurrent.futures import ThreadPoolExecutor
from Classes.Functions import SpecialFunctions
from Classes.SNMP import SNMPFunctions
import Classes.Database as Database
import multiprocessing as mp
from REST_API import REST, database
import schedule as sch
import datetime
import uvicorn
import logging
import time
import json
import os

# Logging configuration
log_file_path = 'logs/main.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a')
    ]
)

# Configration
analysis_database_path = 'databases/analysis.db'
fida_database_path = 'databases/fida.db'
json_alarms_path = 'json/alarms.json'
csv_oid_path = 'csv/Fida OID.csv'
csv_ip_path = 'csv/IPs.csv'
snmp_community = 'public'
fida_working_table = 'working_fida'
server_host = '0.0.0.0'
server_port = 56242

analysis_database = Database.DatabaseFunctions(analysis_database_path)
memory_database = Database.DatabaseFunctions(fida_database_path)
functions = SpecialFunctions()
logger = logging.getLogger()
snmp = SNMPFunctions()
rest = REST()
ips_csv_res = []
oids_list = []
try:
    ips_csv_res = functions.read_csv_data(csv_ip_path)
    oids_list = functions.read_csv_data(csv_oid_path)
except Exception as e:
    logger.exception(f"Error while reading CSV files: {e.args[0]}")

fida_ips_list = [ip[0] for ip in ips_csv_res]
pcs_ips_list = [ip[2] for ip in ips_csv_res]
fida_and_pcs_ips = {}
for ip in ips_csv_res:
    fida_and_pcs_ips[ip[2]] = ip[0]


def main(working_ips):
    read_community = snmp_community
    rest.ips = working_ips
    manager = mp.Manager()
    values = manager.dict({ip: {} for ip in working_ips})
    oids, types, names = zip(*oids_list)

    oid_names_dict = {oids[i]: names[i] for i in range(len(oids))}

    for i in working_ips:
        table_name = f"fida_{i[i.rfind('.') + 1:]}"
        memory_database.create_table(table_name=table_name, attributes={'oid': 'TEXT', 'name': 'TEXT', 'value': 'TEXT'})
        logger.info(f"Table {table_name} created successfully")

    try:
        snmp.get_value_on_multiple_ips(oids, working_ips, read_community, values)
        logger.info('Successfully got values from SNMP')
    except Exception as exp:
        logger.exception(exp.args[0])

    logger.info(f"Values: {values}")

    for ip in values:
        table_name = f"fida_{ip[ip.rfind('.') + 1:]}"
        try:
            conn = memory_database.get_connection()
            cursor = conn.cursor()
            for oid in oids:
                check_query = f"""SELECT COUNT(*) FROM '{table_name}' where oid = '{oid}';"""
                cursor.execute(check_query)
                count = cursor.fetchone()[0]

                if count:
                    memory_database.update_table(table_name, {'value': values[ip][oid]}, {'oid': oid})
                else:
                    memory_database.insert_in_table(table_name, [oid, oid_names_dict[oid], values[ip][oid]])
                logger.info(f"Table {table_name} updated successfully")
            logger.info(f'{ip} : {values[ip]}')
            cursor.close()
            conn.close()
        except Exception as exp:
            logger.exception(f"Error on update table {table_name} with new values: {exp.args[0]}")


@sch.repeat(sch.every().minute)
def ping_pcs_ips():
    name_of_table = 'working_pcs'
    path = json_alarms_path
    database.create_table(name_of_table, {'ip': 'TEXT', 'status': 'TEXT', 'fida_ip': 'TEXT'}, 'ip')
    ping_result = functions.ping(pcs_ips_list)
    down_ips = []
    try:
        for ip in ping_result:
            conn = memory_database.get_connection()
            cursor = conn.cursor()
            count_query = f"""SELECT COUNT(*) FROM {name_of_table} WHERE ip = ?;"""
            cursor.execute(count_query, (ip,))
            count = cursor.fetchone()[0]
            if ping_result[ip] == 'ON':
                if count > 0:
                    memory_database.update_table(name_of_table, {'status': 'ON'}, {'ip': ip})
                else:
                    memory_database.insert_in_table(name_of_table, [ip, 'ON', fida_and_pcs_ips[ip]])
            else:
                down_ips.append(ip)
                if count > 0:
                    memory_database.update_table(name_of_table, {'status': 'OFF'}, {'ip': ip})
                else:
                    memory_database.insert_in_table(name_of_table, [ip, 'OFF', fida_and_pcs_ips[ip]])
        logger.info(f"Table {name_of_table} updated successfully")
    except Exception as exp:
        logger.exception(f"Error while updating table {name_of_table}: {exp.args[0]}")

    try:
        for ip in fida_ips_list:
            data = functions.read_json_data(path)
            if "pc-ping" in data and ip in data["pc-ping"]:
                del data["pc-ping"][ip]
                with open(path, 'w') as json_file:
                    json.dump(data, json_file, indent=4)

        for ip in down_ips:
            dic = {f'{ip}': f'Monitor\'s {fida_and_pcs_ips[ip]} pc with ip {ip} and  is down'}
            SpecialFunctions.update_json_data(path, dic, "pc-ping")

        logger.info(f"JSON file {path} updated successfully")
    except Exception as exp:
        logger.exception(f"Error while updating json file: {exp.args[0]}")


@sch.repeat(sch.every().minute)
def ping_fida_ips():
    try:
        name_of_table = fida_working_table
        database.create_table(name_of_table, {'ip': 'TEXT', 'status': 'TEXT'}, 'ip')
        path = json_alarms_path
        ping_result = functions.ping(fida_ips_list)
        down_ips = functions.update_ping_tables(fida_database_path, name_of_table, ping_result)
        logger.info(f"Table {name_of_table} updated successfully")

        for ip in fida_ips_list:
            data = functions.read_json_data(path)
            if "fida-ping" in data and ip in data["fida-ping"]:
                del data["fida-ping"][ip]
                with open(path, 'w') as json_file:
                    json.dump(data, json_file, indent=4)

        for ip in down_ips:
            dic = {f'{ip}': f'Monitor with ip {ip} is down'}
            SpecialFunctions.update_json_data(path, dic, "fida-ping")

        logger.info(f"JSON file {path} updated successfully")
    except Exception as exp:
        logger.exception(f"Error while pinging FIDA IPs: {exp.args[0]}")


@sch.repeat(sch.every().minute)
def scheduled_func():
    try:
        working_ips_query = memory_database.select_data(fida_working_table)
        working_ips = [ip[0] for ip in working_ips_query if ip[1] == 'ON']
        main(working_ips)
        logger.info('scheduled function successfully executed')
    except Exception as exp:
        logger.exception(f"Error while running main function: {exp.args[0]}")


@sch.repeat(sch.every().hour)
def fill_analysis_table():
    for ip in fida_ips_list:
        analysis_table_name = f"analysis_{ip[ip.rfind('.') + 1:]}"
        fida_table_name = f"fida_{ip[ip.rfind('.') + 1:]}"
        query = f"""select count(*) from sqlite_master where type='table' and name='{analysis_table_name}';"""
        conn = None
        cursor = None

        try:
            conn = analysis_database.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            count = cursor.fetchone()[0]
            if count == 0:
                analysis_database.create_table(analysis_table_name,
                                               {'oid': 'TEXT', 'name': 'TEXT', 'value': 'TEXT',
                                                'DateTime': 'TIMESTAMP'},
                                               'oid, DateTime')

            data = list(database.select_data(fida_table_name))
            for row in data:
                row = list(row)
                row.append(datetime.datetime.now())
                analysis_database.insert_in_table(analysis_table_name, row)
            logger.info(f"Table {analysis_table_name} filled successfully")
        except Exception as exp:
            logger.exception(f"Error while filling analysis table: {exp.args[0]}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    logger.info('Analysis function executed successfully')


@sch.repeat(sch.every().second)
def func():
    rest.update()


def run_scheduler():
    try:
        ping_fida_ips()
    except Exception as exp:
        logger.exception(f"Error while pinging IPs: {exp.args[0]}")
    try:
        ping_pcs_ips()
    except Exception as exp:
        logger.exception(f"Error while pinging on PCs: {exp.args[0]}")
    try:
        scheduled_func()
    except Exception as exp:
        logger.exception(f"Error while running scheduled function: {exp.args[0]}")
    while True:
        sch.run_pending()
        time.sleep(1)


def run_server():
    try:
        uvicorn.run(rest.app, host=server_host, port=server_port)
        logger.info('Server started successfully')
    except Exception as exp:
        logger.exception(f"Error while running server: {exp.args[0]}")


if __name__ == '__main__':
    with ThreadPoolExecutor() as executor:
        executor.submit(run_scheduler)
        executor.submit(run_server)
