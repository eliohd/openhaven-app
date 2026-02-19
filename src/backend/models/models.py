class device():
    def __init__(self, hostname, ip, mac):
        self._hostname = hostname
        self._ipAddress = ip
        self._macAddress = mac

class accessPoint(device):
    def __init__(self, id, hostname, ip, mac, state):
        super().__init__(hostname, ip, mac)
        self.accessPointId = id
        self._state = state

    def toDictionary(self):
        APdata = {'accessPointId': self.accessPointId, 'hostname': self._hostname, 'ipAddress': self._ipAddress, 'macAddress': self._macAddress, 'state': self._state}
        return APdata

class client(device):
    def __init__(self, id, hostname, ip, mac):
        super().__init__(hostname, ip, mac)
        self.clientId = id
        self._active = True

    def toDictionary(self):
        clientData = {'clientId': self.clientId, 'hostname': self._hostname, 'ipAddress': self._ipAddress, 'macAddress': self._macAddress, 'active': self._active}
        return clientData
    
    
class topologyConnection():
    def __init__(self, clientId, accessPointId):
        self._clientId = clientId
        self._accessPointId = accessPointId

    def toDictionary(self):
        topologyData = {'clientId': self._clientId, 'accessPointId': self._accessPointId}
        return topologyData
    
class trafficSample():
    def __init__(self, id, uptimeSec, txRetriesPct, txRateBps, rxRateBps):
        self._accessPointId = id
        self._uptimeSec = uptimeSec
        self._txRetriesPct = txRetriesPct
        self._txRateBps = txRateBps
        self._rxRateBps = rxRateBps

    def toDictionary(self):
        trafficSampleData = {'accessPointId': self._accessPointId, 'uptimeSec': self._uptimeSec, 'txRetriesPct': self._txRetriesPct, 'txRateBps': self._txRateBps, 'rxRateBps': self._rxRateBps}
        return trafficSampleData
    
class wifiBroadcast():
    def __init__(self, id, name, active, hideName):
        self._broadcastId = id
        self._ssid = name
        self._active = active
        self._hideName = hideName
    
    def toDictionary(self):
        wifiBroadcastData = {'broadcastId': self._broadcastId, 'ssid': self._ssid, 'active': self._active, 'hideName': self._hideName}
        return wifiBroadcastData