import httpx
import json
import sqlite3
from src.backend.config import databaseFile

class adminActions:
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
    # additionally, I need to specify the content type, as these are POST actions rather than GET requests
    #https://developer.ui.com/network/v10.1.84/executeadopteddeviceaction
    def _getHeaders(self):
        return {
            'Accept': 'application/json',
            'X-API-Key': self._apiKey,
            'Content-Type': 'application/json'
        }
    
    # Reusable protected method to establish a connection to the database.
    def _dbConnection(self):
        con = sqlite3.connect(databaseFile)
        cur = con.cursor()
        return cur, con
    
    # Protected method that adds a record to the network audit logs table in the database.
    def _createNetworkAuditLog(self, cur, con, id, type, hideNameVal=None):
        if type == "AP":
            # find the name of the AP
            result = cur.execute(
                '''SELECT hostname FROM tbl_APdevices WHERE accessPointId = ?''',
                (id,)
            )
            result = result.fetchone() # gets the result tuple
            # making sure there is a returned result
            if not result:
                # will raise an error which will be caught by the parent method which calls it.
                raise ValueError(f"No accessPoint with id {id}.")

            apName = result[0] # extract the hostname from the result tuple
            message = f"Access point {apName} was restarted." # create the message with the access point's name just fetched
            cur.execute(
                '''INSERT INTO tbl_AuditLogs (accessPointId, logMessage) VALUES (?, ?)''',
                (id, message)
            ) # insert a new audit log record
        elif type == "WIFI":
            #find the ssid of the wifi broadcast
            result = cur.execute(
                '''SELECT ssid FROM tbl_WifiBroadcasts WHERE broadcastId = ?''',
                (id,)
            )
            result = result.fetchone() # gets the result tuple
            #again making sure that there is a result returned
            if not result:
                # again will raise a value error to be caught by the parent method calling it
                raise ValueError(f"Wifi broadcast with id {id} not found - audit log failed.")
            ssid = result[0] # extract the ssid from the result tuple
            message = f"SSID broadcasting for {ssid} has been {'disabled' if hideNameVal else 'enabled'}." # create the message with the wifi broadcast's ssid just fetched
            cur.execute(
                '''INSERT INTO tbl_AuditLogs (logMessage) VALUES (?)''',
                (message,)
            ) # insert a new audit log record, no link to specific access point or wifi broadcast, so null for both FKs.
        # con.commit() will occur in the parent method.

    # Method for the admin to restart a specific access point.
    # using request format from https://developer.ui.com/network/v10.1.84/executeadopteddeviceaction
    def restartAccessPoint(self, deviceId):
        endpoint = f"devices/{deviceId}/actions" # the endpoint URL for the POST request
        payload = json.dumps({
            "action": "RESTART"
        }) # Payload contains the action I want to perform, RESTART the router
        headers = self._getHeaders() # get the headers from the protected method
        url = f"{self._baseURL}/{endpoint}" # form the full endpoint url

        cur, con = self._dbConnection() # establish connection to database for the audit log Method
        try:
            response = self._client.post(url, headers=headers, content=payload) # actually make the POST request to UniFi Network API
            if response.status_code != 200: # if not successful
                return {
                    "successful": False,
                    "message": f"Request to restart access point failed.",
                    "errors": [f"Status code: {response.status_code}", f"Response: {response.text}"]
                } # handles other, unsuccessful response codes from UniFi.
            
            self._createNetworkAuditLog(cur, con, deviceId, "AP")
            con.commit() #commits transaction from the protected method above
            return { # return success message
            "successful": True,
            "message": "Access point is restarting.",
            "errors": []
        } # return success message to main program. The frontend can display this message to the admin within the admin actions dashboard.
        except Exception as error: # Where the request fails altogether.
            return {
                "successful": False,
                "message": f"Restarting the access point failed.",
                "errors": [str(error)]
            }
        finally:
            con.close() # close the database connection

    # this is the Method to enable/disable ssid broadcasting for a wifi broadcast which is stored in tbl_WifiBroadcasts
    def toggleBroadcasting(self, wifiBroadcastId):
        #endpoint for the UniFi Network API
        endpoint = f"wifi/broadcasts/{wifiBroadcastId}"
        # Get the headers from the protected method
        headers = self._getHeaders()
        # Form the base url for the API request
        url = f"{self._baseURL}/{endpoint}"
        
        # payload for the PUT request, need to toggle the hideName boolean value
        # To know its current state, I check the current value in the database.
        cur, con = self._dbConnection() # Establsish db connection
        try:
            result = cur.execute(
            '''SELECT hideName FROM tbl_WifiBroadcasts WHERE broadcastId = ?''',
            (wifiBroadcastId,)
            )
            result = result.fetchone() # get tuple from result

            if not result: # making sure that there is a result, otherwise return error message.
                return{
                    "successful": False,
                    "message": f"Couldn't find wifi broadcast with id {wifiBroadcastId}.",
                    "errors": []
                }
            result = result[0] # get the result from the tuple for the value of hideName currently
            # the value we need to set in the payload below has to be the opposite
            hideNameVal = not bool(result)

            # Creating the payload for the PUT request with the new value for hideName
            payload = json.dumps({
                "hideName": hideNameVal
            })
        
            # Make the PUT request to UniFi Network API
            response = self._client.put(url, headers=headers, content=payload)
            if response.status_code != 200:
                # handle when the response code is not 200, not successful.
                return {
                    "successful": False,
                    "message": f"PUT request to toggle SSID broadcasting failed.",
                    "errors": [f"Status code: {response.status_code}", f"Response: {response.text}"]
                }
            
            # Update the database to reflect the new value for hideName
            cur.execute(
                '''UPDATE tbl_WifiBroadcasts SET hideName = ? where broadcastId = ?''',
                (hideNameVal, wifiBroadcastId)
            )
            # create a network audit log for this action by calling the protected method
            self._createNetworkAuditLog(cur, con, wifiBroadcastId, "WIFI", hideNameVal)
            con.commit() #Commit transaction and save changes for both the hideName update and the audit log record
            # return success message
            return {
                "successful": True,
                "message": f"SSID broadcasting has been {'disabled' if hideNameVal else 'enabled'}.",
                "errors": []
            }
        except Exception as error: # catch all exceptions and return error message
            return {
                "successful": False,
                "message": f"Error occured while toggling ssid broadcasting.",
                "errors": [str(error)]
            }
        finally:
            con.close() # close the database connection