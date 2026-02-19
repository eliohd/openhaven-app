from src.backend.services.unifi_api import APIclient
from src.backend.services.collectData import collectData
from src.backend.config import CONSOLE_IP, API_KEY, SITE_ID

# Create client
client = APIclient(
    consoleIp=CONSOLE_IP,
    apiKey=API_KEY,
    siteId=SITE_ID
)

collector = collectData(client=client)


print("TESTING: Collect AP data")
ap_data, traffic_samples = collector.collectAPData()
for ap in ap_data:
    print(ap)

print("TESTING: Collect AP traffic samples")
for sample in traffic_samples:
    print(sample)

print("TESTING: Collect client data")
client_data, topology_data = collector.collectClientData()
for client_item in client_data:
    print(client_item)

print("TESTING: Collect topology data")
for topology_item in topology_data:
    print(topology_item)

print("TESTING: Collect wifi broadcasts")
wifi_broadcasts = collector.collectWifiBroadcasts()
for broadcast in wifi_broadcasts:
    print(broadcast)

# Close
client.close()