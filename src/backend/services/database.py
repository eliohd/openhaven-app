# importing the collectData class that will allow me to get all the dictionaries of data that will be examined and pushed to the database
from .collectData import collectData

import sqlite3
from src.backend.config import databaseFile

class databaseService():
    def __init__(self, collectDataInstance):
        self._collectData = collectDataInstance
        self._apData = None
        self._trafficSamples = None
        self._clientData = None
        self._topologyData = None

    # establishes connection to the database; I will reuse this throughout my methods, so I made it into its own protected method
    def _dbConnection(self):
        con = sqlite3.connect(databaseFile)
        cur = con.cursor()
        return cur, con
    
    # Method for creating a network audit log based of the events that are detected throughout all of the below processes
    # Optionally pass in the clientId and accessPointId
    def _pushNetworkAuditLog(self, cur, con, message, clientId=None, accessPointId=None):
        try:
            # Insert the log message into tbl_AuditLogs, and optionally if available the clientId, accessPointId, or both
            cur.execute(
                '''INSERT INTO tbl_AuditLogs (logMessage, clientId, accessPointId) VALUES (?, ?, ?)''',
                (message, clientId, accessPointId) 
            )
        except sqlite3.Error as errorMessage:
            print(f"Error inserting network audit log into database: {errorMessage}")

    # this method checks if I already collected the AP and traffic sample data
    # avoids multiple api calls to fetch the same data
    def _fetchAPData(self):
        if self._apData is None or self._trafficSamples is None: # Checking if attributes still do not contain data
            self._apData, self._trafficSamples = self._collectData.collectAPData()
        
    # the simplest data collection and push to db will be traffic samples, as I do not need to do any additional checks, just create new records for all of them
    # traffic samples is historical data

    def pushTrafficSamples(self):
        # as AP data and traffic samples are collected together, I call collectAPData then just use the traffic sample data
        # I conditionally check in the first protected method _fetchAPData to see if I have already collected the data
        # this is because i will need the AP device dictionary later on, and do not want to make another API call as that would be ineffcient
        self._fetchAPData()
        cur, con = self._dbConnection() # Establishes sql connection and cursor
        try:
            for sample in self._trafficSamples: # Loops through each traffic sample in the dictionary of all of them
                cur.execute(
                    '''INSERT INTO tbl_TrafficSamples (accessPointId, uptimeSec, txRetriesPct, txRateBps, rxRateBps) VALUES (?, ?, ?, ?, ?)''', # Inserts each traffic sample into the table
                    (sample['accessPointId'], sample['uptimeSec'], sample['txRetriesPct'], sample['txRateBps'], sample['rxRateBps'])
                )
            con.commit() # Commits the transaction to save changes 
        except sqlite3.Error as errorMessage: # catches any errors that occur in trying to do the above
            print(f"Error inserting traffic sample: {errorMessage}")
            con.rollback() # rolls back the entire operation if one of the inserts fail, that way the database is not partially updated
        finally:
            con.close() # finally, close the connection to the sql database


    def pushAPData(self): # Method to push new access point data to the database
        self._fetchAPData() # Fetches data if not done so already for the APs
        cur, con = self._dbConnection() # establishes sql connection and cursor
        try:
            for ap in self._apData: # Loops through each access point in the dictionary
                cur.execute(
                    '''INSERT INTO tbl_APdevices (accessPointId, hostname, ipAddress, macAddress, apState) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(accessPointId) DO UPDATE SET hostname=excluded.hostname, ipAddress=excluded.ipAddress, macAddress=excluded.macAddress, apState=excluded.apState''',
                    (ap['accessPointId'], ap['hostname'], ap['ipAddress'], ap['macAddress'], ap['state'])
                ) # ON CONFLICT(accessPointId) DO UPDATE SET allows me to update any change in the details of each access point that already exits in the table
                if cur.rowcount == 1: # checking if a new row was inserted from last sql operation
                    message = f"Access point {ap['hostname']} was added to the network."
                else: # otherwise it has just updated an existing record (rowcount 0)
                    message = f"Access point {ap['hostname']} was updated."
                # push the aduit log for the ap and message
                self._pushNetworkAuditLog(con=con, cur=cur, message=message, accessPointId=ap['accessPointId'])
            
            con.commit() # Commits the transaction, saves changes
        except sqlite3.Error as errorMessage: # catches any errors in the operation above
            print(f"Error inserting access point: {errorMessage}")
            con.rollback() # rolls back enitre operation if one fails
        finally:
            con.close() # Closes the connection to the SQL database


    def pushWifiBroadcastData(self): # Method to push new wifi broadcast data into the database
        wifiBroadcasts = self._collectData.collectWifiBroadcasts() # collects all wifi broadcast data using the collectData service
        cur, con = self._dbConnection() # Esatblishes connection to the SQL database and cursor
        try:
            for broadcast in wifiBroadcasts: # looping through each wifi broadcast in the dictionary
                cur.execute(
                    '''INSERT INTO tbl_WifiBroadcasts (broadcastId, ssid, active, hideName) VALUES (?, ?, ?, ?)
                    ON CONFLICT(broadcastId) DO UPDATE SET ssid=excluded.ssid, active=excluded.active, hideName=excluded.hideName''',
                    (broadcast['broadcastId'], broadcast['ssid'], broadcast['active'], broadcast['hideName'])
                ) # ON CONFLICT(broadcastId) DO UPDATE SET works the same as in the pushAPData method, updating any changes in attributes for pre-existing records
                if cur.rowcount == 1: # checks if a new row was inserted from the last INSERT/UPDATE operation
                    message = f"Wifi broadcast {broadcast['ssid']} was added to the network." # Message to say new broadcast was added
                else: # rowcount is 0, so no new insert, just an update of an existing record
                    message = f"Wifi broadcast {broadcast['ssid']} was updated."
                self._pushNetworkAuditLog(con=con, cur=cur, message=message)
            con.commit() # commits the transaction and saves changes
        except sqlite3.Error as errorMessage: # Catches any errors
            print(f"Error inserting wifi broadcast: {errorMessage}")
            con.rollback() # rolls back if one fails
        finally:
            con.close() # closes the connection to the database

    # Checks if client data and topology data have already been collected to prevent the app from making too many API calls
    # these two sets of data are collected together in the collectData service, so I check for both
    def _fetchClientData(self):
        if self._clientData is None or self._topologyData is None:
            self._clientData, self._topologyData = self._collectData.collectClientData()

    def _clientRoamDetected(self, clientId, newAccessPointId, cur, con):
        # Create a network audit log saying that client roamed from ap (currentAPid) to ap (topology['accessPointId'])
        try:
             # Need to fetch the hostnames of each of the involved devices
            apName = cur.execute(
                '''SELECT hostname FROM tbl_APdevices WHERE accessPointId = ?''',
                (newAccessPointId,)
            )
            apName = apName.fetchone()[0] # getting the hostname value from the tuple generated by .fetchone()
            clientName = cur.execute(
                '''SELECT hostname FROM tbl_Clients WHERE clientId = ?''',
                (clientId,)
            )
            clientName = clientName.fetchone()[0] # getting the hostname value from the tuple generated by .fetchone()

            # Create the log message
            message = f"Client {clientName} roamed to AP {apName}."
            # Call the protected method that actually pushes the log into the database
            self._pushNetworkAuditLog(con=con, cur=cur, message=message, clientId=clientId, accessPointId=newAccessPointId)
        except sqlite3.Error as errorMessage:
            print(f"Error creating audit log for client roaming to AP: {errorMessage}")

    # Method to push new or updated client - access point connections to the link table in the database, tbl_Connections
    def pushConnectionData(self):
        self._fetchClientData() # Fetching client and topology data if not done already
        cur, con = self._dbConnection() # Establishes connection to database and cursor
        
        try:
            for topology in self._topologyData: # Loops through each client-AP pair in the dictionary
                # Checking if there is already a record for the client with cliendId in the database
                res = cur.execute(
                    '''SELECT accessPointId FROM tbl_Connections WHERE clientId = ?''',
                    (topology['clientId'],)
                )
                existing = res.fetchone() # .fetchone() will return None if no records, or a tuple of (accessPointId) if there is an existing record
                if existing:
                    currentAPid = existing[0] # extract the value of this accessPointId from the tuple
                    if currentAPid != topology['accessPointId']: # compares the new fetched accessPointId with the current one in the record
                        # updates it to the new accessPointId if they are not the same
                        cur.execute( 
                            '''UPDATE tbl_Connections SET accessPointId = ? WHERE clientId = ?''',
                            (topology['accessPointId'], topology['clientId'])
                        )
                        # Call the protected method clientRoamDetected to create a network audit log for this event
                        self._clientRoamDetected(clientId=topology['clientId'], newAccessPointId=topology['accessPointId'], cur=cur, con=con)
                    else:
                        # there has been no change in the clients parent access point, so no updates to be done
                        pass
                else:
                    # otherwise, there is a new client-AP connection that needs to be inserted as a new record in tbl_Connections
                    cur.execute(
                        '''INSERT INTO tbl_Connections (clientId, accessPointId) VALUES (?, ?)''',
                        (topology['clientId'], topology['accessPointId'])
                    )
                    # create a network audit log saying that a new client roamed to its respective AP
                    self._clientRoamDetected(clientId=topology['clientId'], newAccessPointId=topology['accessPointId'], cur=cur, con=con)

            con.commit() # commits the transaction and saves changes
        except sqlite3.Error as errorMessage: # catches any errors doing the above and the message
            print(f"Error inserting/updating connection data: {errorMessage}")
            con.rollback() # if one fails, entire operation is rolled back, preventing partial updates to the database
        finally:
            con.close() # Finally closes the connection to the database
    
    def pushClientData(self): # Method to push new or updates client data into tbl_Clients
        self._fetchClientData() # fetches client and topology data if not done so already
        cur, con = self._dbConnection() # Establishes connection to database and cursor

        try:
            for client in self._clientData: # Loops through each client in the dictionary
                # Checking for existing record with clientId's that have been fetched and their active status
                res = cur.execute(
                    '''SELECT clientId, active FROM tbl_Clients WHERE clientId = ?''',
                    (client['clientId'],)
                )
                # existing will be None if no existing record for the clientId, or if there is it will be a tuple of (clientId, active)
                existing = res.fetchone()
                if existing:
                    if not existing[1]:  # existing[1] is the active field, I am checking if it is inactive
                        # if inactive in the db, but present in my fetched data, then it is now reconnected. So I update all of its records to reflect this.
                        cur.execute(
                            '''UPDATE tbl_Clients SET hostname = ?, ipAddress = ?, macAddress = ?, active = ? WHERE clientId = ?''',
                            (client['hostname'], client['ipAddress'], client['macAddress'], client['active'], client['clientId'])
                        )
                        # create a network audit log saying that the client with id client['clientId'] is now active again
                        message = f"Client {client['hostname']} connected to the network again."
                        self._pushNetworkAuditLog(con=con, cur=cur, message=message, clientId=client['clientId']) # calls the protected method to push the network audit log to the database
                    else:
                        # In this case, client is already active, so just update any other attributes
                        cur.execute(
                            '''UPDATE tbl_Clients SET hostname = ?, ipAddress = ?, macAddress = ? WHERE clientId = ?''',
                            (client['hostname'], client['ipAddress'], client['macAddress'], client['clientId'])
                        )
                else:
                    # Otherwise, this is a new client and needs to be inserted as new record in tbl_Clients
                    cur.execute(
                        '''INSERT INTO tbl_Clients (clientId, hostname, ipAddress, macAddress, active) VALUES (?, ?, ?, ?, ?)''',
                        (client['clientId'], client['hostname'], client['ipAddress'], client['macAddress'], client['active'])
                    )
                    # create a network audit log saying that a new client with id client['clientId'] was added
                    message = f"New client {client['hostname']} connected to the network."
                    self._pushNetworkAuditLog(con=con, cur=cur, message=message, clientId=client['clientId']) # calls the protected method to push the network audit log to the database
            con.commit() # Commit the transaction and save changes
        except sqlite3.Error as errorMessage: # Catch errors that occur from doing the above
            print(f"Error updating client data: {errorMessage}")
            con.rollback() # roll back if one fails to prevent partial updates
        finally:
            con.close() # close the connection to the database

    def detectInactiveClients(self):
        self._fetchClientData()
        cur, con = self._dbConnection()
        # I need to compare the list of clients I fetched from the API with the list of active clients in the database
        # if the client is in the database as active, but not in the fetched client data, that means it has disconnected
        allClientIds_InFetch = [client['clientId'] for client in self._clientData]
        
        try:
            if allClientIds_InFetch: # Making sure there is at least one client in the above list
                # the following method to check if a client is active in the database but NOT IN the list above
                # I got this method from https://stackoverflow.com/questions/283645/python-list-in-sql-query-as-parameter, @Pi.Lilac
                placeholder = '?'
                placeholders = ', '.join(placeholder for _ in allClientIds_InFetch)
                currentlyActiveRes = cur.execute(
                    '''SELECT clientId FROM tbl_Clients WHERE active = 1 AND clientId NOT IN (%s)''' % placeholders,
                    allClientIds_InFetch
                )
                # produces a list of the active clients in the database that are NOT in the fetched client data
                inactiveClientIds = [row[0] for row in currentlyActiveRes.fetchall()]
                # perform the same method but using IN rather than NOT IN
                if inactiveClientIds:
                    placeholder = '?'
                    placeholders = ', '.join(placeholder for _ in inactiveClientIds)
                    cur.execute(
                        '''UPDATE tbl_Clients SET active = 0 WHERE clientId IN (%s)''' % placeholders,
                        inactiveClientIds
                    )
                    # create a network audit log for each client that was marked as inactive, saying that the client with id clientId was deactivated due to not being detected in the latest client data fetch
                    for clientId in inactiveClientIds: # Looping through each clientId
                        clientName = cur.execute( # fetching the respective hostname for each clientId
                            '''SELECT hostname FROM tbl_Clients WHERE clientId = ?''',
                            (clientId,)
                        )
                        clientName = clientName.fetchone()[0] # getting the hostname value from the tuple generated by .fetchone()
                        # Creating the log message
                        message = f"Client {clientName} disconnected from the network."
                        self._pushNetworkAuditLog(con=con, cur=cur, message=message, clientId=clientId) # call the protected method to push the network audit log to the database

            con.commit() # Commit the transaction and save changes
        except sqlite3.Error as errorMessage: # Catch any errors from doing the above
            print(f"Error detecting inactive clients: {errorMessage}")
            con.rollback() # Roll back all changes if one of the operations fail to prevent partial updates
        finally:
            con.close() # close the connection to the database