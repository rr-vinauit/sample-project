from typing import List
import mysql.connector
from mysql.connector.pooling import PooledMySQLConnection
from table_row import TableRow
import os
from dotenv import load_dotenv


class database:

    conn: PooledMySQLConnection

    def __init__(self):
        load_dotenv()
        self.conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD')
        )

    def get_connection(self):
        return self.conn

    def make_select_query(self, query):
        c = self.conn.cursor()
        c.execute(query)
        return c.fetchall()

    def make_insert_many_query(self, query: str, params: List[TableRow], reference_id: str) -> None:

        c = self.conn.cursor()
        c.executemany(query, [p.to_database_representation() for p in params])

        try:
            self.conn.commit()
        except:
            self.conn.rollback()
            print("Insertion #{id} Failed".format(id=reference_id))
