import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# tests the creation or updating of toplogy connection records for clients and access points in link table tbl_Connections

# v2 - there now is a network audit log for when a client roams to a specific access point

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

print("Pushing (or updating) client and access point topology connections...")
print("Generating network audit logs for any client roaming to access points...")
db.pushConnectionData()
print("Done.")
