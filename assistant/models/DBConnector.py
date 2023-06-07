import sqlite3
from pathlib import Path
from assistant import logger


memory_path = './data/memory.db'

class DBConnector():
    def __init__(self) -> None:
        path = Path(memory_path)
        if not path.exists():
            path.touch()

        conn, cursor = self._get_connection()
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS messages (
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                message TEXT NOT NULL
            )
        '''
        cursor.execute(create_table_query)
        conn.commit()
        self._close_connection(conn, cursor)
        logger.info('database loaded')
    
    def retrive_history(self, limit: int = 30) -> list[str]:
        conn, cursor = self._get_connection()
        select_query = f'SELECT * FROM messages ORDER BY rowid DESC LIMIT {limit}'
        cursor.execute(select_query)
        result = [row[1] for row in cursor.fetchall()[::-1]]
        self._close_connection(conn, cursor)
        return result
    
    def add_to_history(self, message: str):
        conn, cursor = self._get_connection()
        query = 'INSERT INTO messages (message) VALUES (?)'
        cursor.execute(query, (message,))
        conn.commit()
        self._close_connection(conn, cursor)


    def _get_connection(self):
        conn = sqlite3.connect(memory_path)
        cursor = conn.cursor()
        return conn, cursor
    
    def _close_connection(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        cursor.close()
        conn.close()