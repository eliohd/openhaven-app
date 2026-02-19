-- the database schema for the network insights dashboard

-- tbl_APdevices
-- stores access point information
CREATE TABLE IF NOT EXISTS tbl_APdevices (
    accessPointId CHAR(36) PRIMARY KEY,
    hostname VARCHAR(50) NOT NULL,
    -- https://stackoverflow.com/questions/1434298/sql-server-equivalent-to-mysql-enum-data-type
    apState TEXT DEFAULT 'OFFLINE' CHECK(apState IN ('ONLINE', 'OFFLINE', 'UPDATING', 'GETTING_READY', 'CONNECTION_INTERRUPTED')),
    ipAddress VARCHAR(15) NOT NULL,
    macAddress VARCHAR(17) UNIQUE NOT NULL
);

-- tbl_Clients
-- stores client information
CREATE TABLE IF NOT EXISTS tbl_Clients (
    clientId CHAR(36) PRIMARY KEY,
    hostname VARCHAR(50) NOT NULL,
    ipAddress VARCHAR(15) NOT NULL,
    macAddress VARCHAR(17) UNIQUE NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    connectedAt DATETIME NOT NULL
);

-- tbl_Connections
-- stores connection information useful for topology for ap devices and clients
CREATE TABLE IF NOT EXISTS tbl_Connections (
    clientId CHAR(36) NOT NULL,
    accessPointId CHAR(36) NOT NULL,
    PRIMARY KEY (clientId, accessPointId),
    FOREIGN KEY (clientId) REFERENCES tbl_Clients(clientId) ON DELETE CASCADE,
    FOREIGN KEY (accessPointId) REFERENCES tbl_APdevices(accessPointId) ON DELETE CASCADE
);

-- tbl_Users
-- stores user information for access to the dahsboard
CREATE TABLE IF NOT EXISTS tbl_Users (
    username VARCHAR(50) PRIMARY KEY,
    passwordHash VARCHAR(255) NOT NULL,
    accountType TEXT NOT NULL CHECK(accountType IN ('ADMIN', 'MEMBER'))
);

-- tbl_AuditLogs
-- stores log messages for different events in the app
CREATE TABLE IF NOT EXISTS tbl_AuditLogs (
    auditLogId INTEGER PRIMARY KEY AUTOINCREMENT,
    accessPointId CHAR(36),
    clientId CHAR(36),
    -- deviceType was removed as this can be derived from whether the clientId or accessPointId is not null
    dateCreated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- https://stackoverflow.com/questions/10720486/date-timestamp-to-record-when-a-record-was-added-to-the-table
    logMessage TEXT NOT NULL,
    FOREIGN KEY (accessPointId) REFERENCES tbl_APdevices(accessPointId) ON DELETE SET NULL,
    FOREIGN KEY (clientId) REFERENCES tbl_Clients(clientId) ON DELETE SET NULL
    -- log should only reference a client or an access point, not both
    -- uses a check constraint to make sure only one is not null, or both are null
    -- both can be null if parent node (client or ap) is deleted, or if it is just a general log
    CHECK (
        (accessPointId IS NOT NULL AND clientId IS NULL) OR
        (accessPointId IS NULL AND clientId IS NOT NULL) OR
        (accessPointId IS NULL AND clientId IS NULL)
    )
);

-- tbl_TrafficSamples
-- stores real-time samples for each access point fetched periodically
CREATE TABLE IF NOT EXISTS tbl_TrafficSamples (
    sampleId INTEGER PRIMARY KEY AUTOINCREMENT,
    accessPointId CHAR(36) NOT NULL,
    uptimeSec INT NOT NULL,
    txRetriesPct FLOAT NOT NULL,
    txRateBps INT NOT NULL,
    rxRateBps INT NOT NULL,
    dateCreated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, -- https://www.sqlitetutorial.net/sqlite-date-functions/sqlite-current_timestamp/
    FOREIGN KEY (accessPointId) REFERENCES tbl_APdevices(accessPointId) ON DELETE CASCADE
);

-- tbl_WifiBroadcasts
-- stores a list of the different wifi broadcasts
-- useful for when disabling/enabling ssid broadcasting in admin dashboard
CREATE TABLE IF NOT EXISTS tbl_WifiBroadcasts (
    broadcastId CHAR(36) PRIMARY KEY,
    ssid VARCHAR(50) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    hideName BOOLEAN NOT NULL
);

-- tbl_Settings
-- stores retention settings for historical data
CREATE TABLE IF NOT EXISTS tbl_Settings (
    settingId INT PRIMARY KEY,
    -- retention period can either be 7, 30, 90 or null so that data is never deleted
    retentionPeriod INT CHECK(retentionPeriod in (7, 30, 90) OR retentionPeriod IS NULL),
    lastDeletion DATETIME
);

-- index lists for when searching through the data ADD LATER

-- default settings
INSERT OR IGNORE INTO tbl_Settings (settingId, retentionPeriod) 
VALUES (1, 30);