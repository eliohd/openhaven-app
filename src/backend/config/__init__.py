# loads configuration from .\config.py

from .config import (
    API_KEY,
    CONSOLE_IP,
    SITE_ID,
    projectRoot,
    dataFolder,
    databaseFile,
    FETCH_INTERVAL
)

__all__ = [
    'API_KEY',
    'CONSOLE_IP',
    'SITE_ID',
    'projectRoot',
    'dataFolder',
    'databaseFile',
    'FETCH_INTERVAL'
]