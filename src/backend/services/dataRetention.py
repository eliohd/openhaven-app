import sqlite3
from src.backend.config import databaseFile
from datetime import datetime, timedelta

class dataRetention:
    def __init__(self):
        pass

    def _dbConnection(self):
        con = sqlite3.connect(databaseFile)
        cur = con.cursor()
        return cur, con
    
    def _getRetentionPeriod(self):
        cur, con = self._dbConnection()
        try:
            result = cur.execute(
                '''SELECT retentionPeriod FROM tbl_Settings WHERE settingId = 1'''
            )
            result = result.fetchone()
            if result:
                return result[0]
            else:
                return 30 # this is the default retention period, should already be in the database by default from schema definition
        finally:
            con.close()
    
    def setRetentionPeriod(self, value):
        cur, con = self._dbConnection()
        try:
            cur.execute(
                '''UPDATE tbl_Settings SET retentionPeriod = ? WHERE settingId = 1''',
                (value,)
            )
            con.commit()
            return {
                "successful": True,
                "message": f"Retention period changed to {value} days.",
                "errors": []
            }
        except Exception as error:
            return {
                "successful": False,
                "message": "Couldn't update retention period.",
                "errors": [str(error)]
            }
        finally:
            con.close()

    def _deleteOldLogs(self, cur, con, cutoffDateStr):
        cur.execute(
            '''DELETE FROM tbl_AuditLogs WHERE dateCreated < ?''',
            (cutoffDateStr,)
        )

    def _deleteOldSamples(self, cur, con, cutoffDateStr):
        cur.execute(
            '''DELETE FROM tbl_TrafficSamples WHERE dateCreated < ?''',
            (cutoffDateStr,)
        )

    def deleteOldData(self):
        cur, con = self._dbConnection()

        try:
            retentionPeriod = self._getRetentionPeriod()
             # Need to first calculate the cutoff date
            # https://stackoverflow.com/questions/441147/how-to-subtract-a-day-from-a-date
            cutoffDate = datetime.now() - timedelta(days=retentionPeriod)
            # Convert the date to a string format to be used in the SQL query
            # https://docs.python.org/3/library/datetime.html#datetime.datetime.strftime
            cutoffDateStr = cutoffDate.strftime("%Y-%m-%d %H:%M:%S")

            self._deleteOldLogs(cur, con, cutoffDateStr)
            self._deleteOldSamples(cur, con, cutoffDateStr)
            con.commit()

            # get the number of logs deleted
            # https://database.guide/2-ways-to-return-the-number-of-rows-changed-by-a-sql-statement-in-sqlite/
            numLogsDeleted = cur.execute(
                '''SELECT changes()'''
            )
            numLogsDeleted = numLogsDeleted.fetchone()[0] # get the integer value from the result tuple returned
            return {
                "successful": True,
                "message": f"Deleted {numLogsDeleted} old network audit logs and traffic samples.",
                "errors": [],
            }
        except Exception as error:
            return {
                "successful": False,
                "message": f"Error while deleting old data from db.",
                "errors": [str(error)],
            }
        finally:
            con.close()
        