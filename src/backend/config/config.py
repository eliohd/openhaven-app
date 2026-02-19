# this will have configurations for the backend of the application
# provides easy access to environment variables and other variables which will be reused extensively throughout all the code

import os
from pathlib import Path
# to manage environment variables, I will use the python-dotenv library, following https://www.geeksforgeeks.org/python/using-python-environment-variables-with-python-dotenv/
from dotenv import load_dotenv

# set up the project's root, the data folder file path, and the database file path
projectRoot = Path(__file__).parent.parent.parent.parent
dataFolder = projectRoot / 'data'
databaseFile = dataFolder / 'database.db'

# load environment vars from .env file
envPath = projectRoot / '.env'
load_dotenv(envPath)

# get the API key and Site ID from the env vars
# the site id is used by UniFi to specify the specific network 'site' I want to retrieve data from; this is retrieved from the UniFi dashboard
API_KEY = os.getenv('API_KEY')
CONSOLE_IP = os.getenv('CONSOLE_IP')
SITE_ID = os.getenv('SITE_ID')

# constants that will be used for the database
FETCH_INTERVAL = 300 #time between making API calls for new data - 5 mins

if __name__ == "__main__":
    # for testing:
    print(f"Project root: {projectRoot}")
    print(f"Data folder: {dataFolder}")
    print(f"Database file: {databaseFile}")
    print(f"API Key: {API_KEY}")
    print(f"Console IP: {CONSOLE_IP}")
    print(f"Site ID: {SITE_ID}")

