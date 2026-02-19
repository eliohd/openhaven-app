#http client that allows me to communicate with the network API using HTTP GET requests
import httpx

# this class will allow me to easily make api calls for different endpoints across the app
class APIclient:
    # constructor which defines the base url from the console ip and site id
    def __init__(self, consoleIp, apiKey, siteId):
        self._consoleIp = consoleIp
        self._apiKey = apiKey
        self._siteId = siteId
        self._baseURL = f"https://{self._consoleIp}/proxy/network/integration/v1/sites/{self._siteId}"

        # creating a http client for efficiency, can then close this client when I am done with a request
        # that way I do not build up a bunch of open HTTP clients that are making requests
        # https://www.python-httpx.org/advanced/clients/
        self._client = httpx.Client(verify=False)

    # from the UniFi network API documentation, I need to have these custom headers that include the API key and say i want a json response
    # protected mehtod - i will only need this from within the class
    def _getHeaders(self):
        return {
            'Accept': 'application/json',
            'X-API-Key': self._apiKey
        }
    
    # i will use this method to make get requests for multiple endpoints
    # eg I will need to make requests for clients, access points, traffic samples, which can all reuse this core make request method
    # again, protected method, I will only need this from within the class
    def _makeRequest(self, endpoint):
        #gets headers from protected method
        headers = self._getHeaders()
        # forms base url using endpoint passed in
        url = f"{self._baseURL}/{endpoint}"

        # i use a try except statement to catch any errors while fetching data
        try:
            response = self._client.get(url, headers=headers)

            # code 200 would mean it is successful, i can correctly return the response json
            if response.status_code == 200:
                return response.json()
            else: # otherwise i can retrieve what response code i actually got, and the message with it
                print(f"Request to network api failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
            
        # catch the exception message as well if it fails altogether, this would mean somethng is fundamentally wrong with the request method
        except Exception as exceptionMessage:
            print(f"Error making a request: {exceptionMessage}" )
            return None


    # fetching all of the required data as set out in the hierarchy chart in 2.5, and the flowcharts in 2.2.2
    # these are all public methods

    # fetching all of the access points on the network, will return a json file with all of the APs
    def fetchAccessPoints(self):
        endpoint = "devices"
        response = self._makeRequest(endpoint)

        #in the response format, it is a dictionary, where the array 'data' contains all of the ap objects
        # response format from https://developer.ui.com/network/v10.1.84/getadopteddeviceoverviewpage
        deviceList = response['data']
        return deviceList

    
    # to fetch all of the clients, same method as above
    def fetchClients(self):
        endpoint = "clients"
        response = self._makeRequest(endpoint)

        # response format same as the ap format above
        # https://developer.ui.com/network/v10.1.84/getconnectedclientoverviewpage
        clientList = response['data']
        return clientList
    
    # to fetch what router each client is connected to, I GET the details for the specific client specified with clientId
    def fetchTopology(self, clientId):
        endpoint = f"clients/{clientId}"
        response = self._makeRequest(endpoint)

        # data is returned per client, so format is different
        #https://developer.ui.com/network/v10.1.84/getconnectedclientdetails
        return response
    
    # fetching live device statistics for each access point, specified by deviceId
    def fetchTrafficSample(self, deviceId):
        endpoint = f"devices/{deviceId}/statistics/latest"
        response = self._makeRequest(endpoint)
        
        # want the raw json, format similar to above
        return response
    
    # fetching a list of all the wifi broadcasts, used to help create the admin dashboard
    # in the admin dash, we will then be able to do POST requests with the specific wifiId to enable/disable SSID broadcasting
    def fetchWifiBroadcasts(self):
        endpoint = "wifi/broadcasts"
        response = self._makeRequest(endpoint)

        # need to extract the data like the ap's and clients
        #https://developer.ui.com/network/v10.1.84/getwifibroadcastpage
        wifiList = response['data']
        return wifiList
    
    # the hideName (ssid broadcasting) attribute for a wifi broadcast is not included in the api request that lists all of the broadcasts
    # thus i made another method that fetches the details of each one, which will be called by the collectData.py
    def fetchBroadcastDetails(self, id):
        endpoint = f"wifi/broadcasts/{id}"
        response = self._makeRequest(endpoint)
        
        #want the raw json
        return response
