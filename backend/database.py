import mysql.connector
from mysql.connector import Error
from config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    """MySQL Database Connection Handler"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                port=Config.MYSQL_PORT
            )
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info("✓ Database connection successful")
            return True
        except Error as e:
            logger.error(f"✗ Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            logger.info("✓ Database connection closed")
    
    def execute_query(self, query, params=None):
        """Execute SELECT query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"✗ Query execution error: {e}")
            return None
    
    def execute_insert_update(self, query, params=None):
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.rowcount
        except Error as e:
            self.connection.rollback()
            logger.error(f"✗ Insert/Update error: {e}")
            return None
    
    def get_last_insert_id(self):
        """Get last inserted row ID"""
        return self.cursor.lastrowid

# Global database instance
db = Database()