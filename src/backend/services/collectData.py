from ..models.models import accessPoint, client, topologyConnection, trafficSample, wifiBroadcast
from .unifi_api import APIclient

class collectData:

    def __init__(self, apiClient = APIclient):
        if apiClient is None:
            raise ValueError("API client instance is required")
        self._api = apiClient

    def _collectTrafficSample(self, id, state):
        trafficSampleJSON = self._api.fetchTrafficSample(id)
       # response format https://developer.ui.com/network/v10.1.84/getadopteddevicelateststatistics
        if state != "ONLINE":
            trafficSampleObject = trafficSample(id=id, uptimeSec=0, txRetriesPct=0, txRateBps=0, rxRateBps=0)
        else:
            trafficSampleObject = trafficSample(id=id, uptimeSec=trafficSampleJSON['uptimeSec'], txRetriesPct=trafficSampleJSON['interfaces']['radios'][0]['txRetriesPct'], txRateBps=trafficSampleJSON['uplink']['txRateBps'], rxRateBps=trafficSampleJSON['uplink']['rxRateBps'])
        trafficSampleDict = trafficSampleObject.toDictionary()

        return trafficSampleDict

    def collectAPData(self):
        allDevices = self._api.fetchAccessPoints()
        apData = []
        trafficSamples = []
        for device in allDevices:
            ap = accessPoint(id=device['id'], hostname=device['name'], ip=device['ipAddress'], mac=device['macAddress'], state=device['state'])
            apDict = ap.toDictionary()

            trafficSampleDict = self._collectTrafficSample(ap.accessPointId, device['state'])
            apData.append(apDict)
            trafficSamples.append(trafficSampleDict)

        return apData, trafficSamples

    def _collectTopology(self, id):
        perClientData = self._api.fetchTopology(clientId=id)
        #extract the client's id, and then its 'uplink' id, which is the id of the router it is connected to
        toplogy = topologyConnection(clientId=perClientData['id'], accessPointId=perClientData['uplinkDeviceId'])
        topologyDict = toplogy.toDictionary()
        return topologyDict
    

    def collectClientData(self):
        allClients = self._api.fetchClients()
        clientData = []
        topologyData = []
        for device in allClients:
            ip_address = device.get('ipAddress') or "Unknown"
            clientDevice = client(id=device['id'], hostname=device['name'], ip=ip_address, mac=device['macAddress'])
            clientDict = clientDevice.toDictionary()

            topologyDict = self._collectTopology(clientDevice.clientId)
            clientData.append(clientDict)
            topologyData.append(topologyDict)
        return clientData, topologyData
        
    def collectWifiBroadcasts(self):
        allWifiBroadcasts = self._api.fetchWifiBroadcasts()
        wifiBroadcastData = []
        for broadcast in allWifiBroadcasts:
            # fetch the broadcast's details, primarily to get whether ssid broadcasting is enabled/disabled
            broadcastDetails = self._api.fetchBroadcastDetails(broadcast['id'])
            wifiBroadcastObject = wifiBroadcast(id=broadcast['id'], name=broadcast['name'], active=broadcast['enabled'], hideName=broadcastDetails['hideName'])

            wifiBroadcastDict = wifiBroadcastObject.toDictionary()
            wifiBroadcastData.append(wifiBroadcastDict)

        return wifiBroadcastData