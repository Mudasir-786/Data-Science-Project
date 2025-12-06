# Database helper function
import sqlite3
import os

def get_db_path():
    """Get the absolute path to the database file"""
    return os.path.join(os.path.dirname(__file__), '..', 'aqi_history.db')

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(get_db_path())
