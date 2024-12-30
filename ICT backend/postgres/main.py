import schedule as sch
import requests
import psycopg2
import sqlite3
import logging
import time
import os

log_file_path = '/analysis/postgres/logs/main.log'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a')
    ]
)

logger = logging.getLogger()


def __main__():
    logger.info("Starting the process")
    routes_names = []

    try:
        database_user = os.getenv('POSTGRES_ANALYSIS_USER')
        database_password = os.getenv('POSTGRES_ANALYSIS_PASSWORD')
        database_name = os.getenv('POSTGRES_ANALYSIS_DB')
        database_host = os.getenv('GLOBAL_HOST')

        postgres_connection = psycopg2.connect(database=database_name, user=database_user, password=database_password,
                                               host=database_host,
                                               port='56433')
        postgres_cursor = postgres_connection.cursor()
        logger.info("Connected to the database")
    except Exception as e:
        logger.exception(f"Error while connecting to the database: {str(e)}")
        return

    try:
        routes = requests.get('http:// {os.getenv("GLOBAL_HOST")}:8001/routes')
        routes = routes.json()
        for i in routes['data']:
            routes_names.append(i['name'])
            route_name = i['name']
            url = f"http://{os.getenv("GLOBAL_HOST")}:8000/{route_name}/analysis-file"
            response = requests.get(url)
            if response.status_code == 200:
                with open(f'/analysis/postgres/databases copy/{route_name}.db', 'wb') as f:
                    f.write(response.content)
                logger.info(f"File {route_name}.db downloaded successfully.")
            else:
                logger.exception(
                    f"Failed to download the file. Status code: {response.status_code} \n Response Content: {response.content.decode('utf-8', errors='ignore')}")
    except Exception as e:
        logger.exception(f"Error while fetching routes: {str(e)}")
        return

    for route in routes_names:
        try:
            postgres_cursor.execute(f"""
                CREATE SCHEMA IF NOT EXISTS {route};
                """)
            postgres_connection.commit()
            postgres_cursor.execute(f'SET search_path TO {route};')
            postgres_connection.commit()
        except Exception as e:
            logger.exception(f"Error while creating schema: {str(e)}")
            return

        try:
            try:
                sqlite_connection = sqlite3.connect(f'/analysis/postgres/databases copy/{route}.db')
                sqlite_cursor = sqlite_connection.cursor()
                sqlite_cursor.execute("SELECT name,sql FROM sqlite_master WHERE type='table';")
                result = sqlite_cursor.fetchall()
                if not result:
                    logger.error(f"No tables found in {route}.db")
                    continue
                logger.info(f"Tables found in {route}.db")
            except Exception as e:
                logger.exception(f"Error while connecting to the database: {str(e)}")
                return

            for table_name, creat_table_query in result:
                try:
                    postgres_cursor.execute(f"""
                            select 1 from information_schema.tables where table_name = '{table_name}';
                        """)
                    table_exists = postgres_cursor.fetchone()
                    if not table_exists:
                        postgres_cursor.execute(creat_table_query)
                        postgres_connection.commit()
                    logger.info(f"Table {table_name} created successfully.")
                except Exception as e:
                    logger.exception(f"Error while creating table: {str(e)}")

                sqlite_cursor.execute(f"SELECT * FROM {table_name};")
                devices = sqlite_cursor.fetchall()
                get_sqlite_info = sqlite_cursor.execute(f"PRAGMA table_info({table_name});"
                                                        ).fetchall()
                keys = [(column[0], column[1]) for column in get_sqlite_info if column[5] != 0]
                pk = keys[0][1]
                datetime_key = keys[1][1]
                for device in devices:
                    placeholders = ', '.join(['%s'] * len(device))
                    check = f'SELECT 1 FROM "{table_name}" WHERE {pk} = \'{device[0]}\' AND {datetime_key} = \'{device[int(keys[1][0])]}\''
                    postgres_cursor.execute(check)
                    exists = postgres_cursor.fetchone()
                    if exists:
                        continue
                    postgres_cursor.execute(f'INSERT INTO "{table_name}" VALUES ({placeholders});', device)
                postgres_connection.commit()
                logger.info(f"Data for table {table_name} in {route} inserted successfully.")
        except Exception as e:
            logger.exception(f"Error : {str(e)}")

        try:
            delete_url = f"http://{os.getenv("GLOBAL_HOST")}:8000/{route}/delete/analysis-file"
            response = requests.delete(delete_url)
            if response.content == f'Analysis file deleted successfully':
                logger.info(f"Analysis file {route}.db deleted successfully.")
            os.remove(f'/analysis/postgres/databases copy/{route}.db')
            logger.info(f"File {route}.db deleted successfully")
        except Exception as e:
            logger.exception(f"Error while deleting file: {str(e)}")
            return


sch.every().day.at("00:00").do(__main__)

if __name__ == '__main__':
    while True:
        sch.run_pending()
        time.sleep(1)
