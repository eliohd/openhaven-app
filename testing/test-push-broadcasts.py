import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# tests the creation of new records or updates existing records for wifi broadcasts colleccted in each fetch

#v2 - There should be a network audit log for any new wifi broadcasts added, or any updates to an existing broadcast

# establishes the api client, the data collector, and the database service
# all three of these imports are services I created in my services folder in the backend
# together, they allow me to fetch from the UniFi Network API, organise the data, and push it to the SQLite database
from src.backend.services.unifi_api import APIclient
from src.backend.services.collectData import collectData
from src.backend.services.database import databaseService
from src.backend.config import CONSOLE_IP, API_KEY, SITE_ID

# creates the client object for APIclient using the environment variables which we defined in the config file
client = APIclient(
    consoleIp=CONSOLE_IP,
    apiKey=API_KEY,
    siteId=SITE_ID
)

# this is the data collector instance/object which uses the client defined above
collector = collectData(apiClient=client)
# finally the database service instance/object to push the data to the database, using the collector to help
db = databaseService(collectDataInstance=collector)

print("Pushing wifi broadcasts (or updating) to the database...")
# now there should be network audit logs
print("Generating any network audit logs....")
db.pushWifiBroadcastData()
print("Done.")
