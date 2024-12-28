import os
import sqlite3 as sql


class DatabaseFunctions:

    # Initialize the database connection
    def __init__(self, db_path):
        self.db_path = db_path

    def get_connection(self):
        dir_path = os.path.dirname(self.db_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return sql.connect(self.db_path)

    # DDL operations
    # Create a table in the database
    def create_table(self, table_name, attributes, primary_key=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            columns = ', '.join([f"{col} {dtype}" for col, dtype in attributes.items()])
            primary_key_clause = f', PRIMARY KEY ({primary_key})' if primary_key else ''
            create_table_query = f"""CREATE TABLE IF NOT EXISTS "{table_name}" (
                                    {columns}
                                    {primary_key_clause}
                                    );"""
            if not isinstance(create_table_query, str):
                create_table_query = str(create_table_query)
            cursor.execute(create_table_query)
        except Exception as e:
            raise Exception(f'Error while creating table {table_name} : {e}')
        finally:
            cursor.close()
            conn.close()

    # Drop a table from the database
    def drop_table(self, table_name):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            check_query = f"""SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"""
            if not isinstance(check_query, str):
                check_query = str(check_query)
            table_exists = cursor.execute(check_query).fetchone()

            if table_exists:
                drop_table_query = f"""DROP TABLE '{table_name}';"""
                if not isinstance(drop_table_query, str):
                    drop_table_query = str(drop_table_query)
                cursor.execute(drop_table_query)
            else:
                raise Exception(f'Table {table_name} does not exist')

        except Exception as e:
            raise Exception(f'Error while dropping table {table_name} : {e}')
        finally:
            cursor.close()
            conn.close()

    # DML operations
    # Insert data into the table
    def insert_in_table(self, table_name, data):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            values = ', '.join([f"'{value}'" for value in data])
            insert_query = f"""
                INSERT INTO "{table_name}" values ({values});
                """
            if not isinstance(insert_query, str):
                insert_query = str(insert_query)
            cursor.execute(insert_query)
            conn.commit()
        except Exception as e:
            raise Exception(f'Error while inserting data on table {table_name} : {e}')
        finally:
            cursor.close()
            conn.close()

    # Update data in the table
    def update_table(self, table_name, data, filter_dic):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            set_data = ', '.join([f"{key} = '{value}'" for key, value in data.items()])
            filter_data = ' AND '.join([f"{key} = '{value}'" for key, value in filter_dic.items()])
            update_query = f"""UPDATE "{table_name}" SET {set_data} WHERE {filter_data};"""
            if not isinstance(update_query, str):
                update_query = str(update_query)
            cursor.execute(update_query)
            conn.commit()
        except Exception as e:
            raise Exception(f'Error while updating data on table {table_name} : {e}')
        finally:
            cursor.close()
            conn.close()

    # Delete data from the table
    def delete_from_table(self, table_name, filter_dic=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Check if the table exists
            check_query = f"""SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"""
            if not isinstance(check_query, str):
                check_query = str(check_query)
            cursor.execute(check_query)
            table_exists = cursor.fetchone()

            if table_exists:
                filter_data = ' AND '.join(
                    [f"{key} = '{value}'" for key, value in filter_dic.items()]) if filter_dic else '1=1'
                delete_query = f"""DELETE FROM "{table_name}" WHERE {filter_data};"""
                if not isinstance(delete_query, str):
                    delete_query = str(delete_query)
                cursor.execute(delete_query)
                conn.commit()
            else:
                raise Exception(f'Table {table_name} does not exist')

        except Exception as e:
            raise Exception(f'Error while deleting data from table {table_name}: {e}')
        finally:
            cursor.close()
            conn.close()

    # DQL operations
    # Get all data from the table
    def select_data(self, table_name):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = f"""SELECT * FROM "{table_name}" """
            if not isinstance(query, str):
                query = str(query)
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            raise Exception(f'Error while getting all data from table {table_name} : {e}')
        finally:
            cursor.close()
            conn.close()

    # Get data from the table with filter
    def select_data_with_filter(self, table_name, filter_dic):
        conn = self.get_connection()
        cursor = conn.cursor()
        filter_data = ' AND '.join([f"{key} = '{value}'" for key, value in filter_dic.items()])
        try:
            query = f"""SELECT * FROM "{table_name}" WHERE {filter_data} """
            if not isinstance(query, str):
                query = str(query)
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            raise Exception(f'Error while getting all data from table {table_name} with filters {filter_data} : {e}')
        finally:
            cursor.close()
            conn.close()

    # execute a custom query
    def execute_custom_query(self, query):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if not isinstance(query, str):
                query = str(query)
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            raise Exception(f'Error while executing query : {e}')
        finally:
            cursor.close()
            conn.close()
