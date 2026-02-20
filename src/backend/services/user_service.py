import sqlite3
from src.backend.config import databaseFile

from argon2 import PasswordHasher

class UserService():
    def __init__(self):
        pass

    def _dbConnection(self):
        con = sqlite3.connect(databaseFile)
        cur = con.cursor()
        return cur, con
    
    def _hashPassword(self, password):
        ph = PasswordHasher()
        hashedPassword = ph.hash(password)
        return hashedPassword
    
    def _validatePassword(self, password):
        valid = True
        errors = []
        if len(password) < 8:
            valid = False
            errors.append("Password must be at least 8 characters long.")
        if not any(char.isupper() for char in password):
            valid = False
            errors.append("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in password):
            valid = False
            errors.append("Password must contain at least one lowercase letter.")
        if not any(char.isdigit() for char in password):
            valid = False
            errors.append("Password must contain at least one number")
        
        special = "@!£$%^&*;()?{}#:,.<>"
        if not any(char in special for char in password):
            valid = False
            errors.append("Password must contain at least one special character")
        return valid, errors
    
    def _userExists(self, username):
        cur, con = self._dbConnection()
        try:
            result = cur.execute(
                '''SELECT COUNT(*) FROM tbl_Users WHERE LOWER(username) = LOWER(?)''',
                (username,)
            )
            result = result.fetchone()[0]
            if result > 0:
                return True
            else:
                return False
        finally:
            con.close()

    def createUser(self, username, password, accessLevel):
        if accessLevel not in ['ADMIN', 'MEMBER']:
            return {
                "successful": False,
                "message": "User access level must be ADMIN or MEMBER.",
                "errors": ['Invalid user access level.']
            }
        if self._userExists(username):
            return {
                "successful": False,
                "message": "This username already exists.",
                "errors": ['This username already exists.']
            }
        valid, errors = self._validatePassword(password)
        if not valid:
            return {
                "successful": False,
                "message": "Requirements for password not met",
                "errors": errors
            }
        
        # from here onwards the account details are verified and can now create the user
        hashedPassword = self._hashPassword(password)

        cur, con = self._dbConnection()
        try:
            cur.execute(
                '''INSERT INTO tbl_Users (username, passwordHash, accessLevel) VALUES (?, ?, ?)''',
                (username.lower(), hashedPassword, accessLevel)
            )
            con.commit()
            return {
                "successful": True,
                "message": f"User {username} created successfully.",
                "errors": []
            }
        except Exception as error:
            return {
                "successful": False,
                "message": f"Error creating new user.",
                "errors": [str(error)]
            }
        finally:
            con.close()

    def authenticate(self, username, password):
        cur, con = self._dbConnection()
        try:
            result = cur.execute(
                '''SELECT userId, username, passwordHash, accessLevel FROM tbl_Users WHERE LOWER(username) = LOWER(?)''',
                (username,)
            )

            result = result.fetchone()
            if not result:
                return {
                    "successful": False,
                    "message": "Username or password is invalid.",
                    "errors": ["Username or password is invalid."] 
                }
            
            db_userId, db_username, passwordHash, accessLevel = result
            ph = PasswordHasher()
            ph.verify(passwordHash, password)
            return {
                "successful": True,
                "message": f"Login successful, welcome {db_username}!",
                "errors": [],
                "data": {
                    'username': db_username,
                    'accessLevel': accessLevel
                }
            }
        except Exception as error:
            return {
                "successful": False,
                "message": "Username or password is invalid.",
                "errors": [str(error)]
            }
        finally:
            con.close()

    def getUserByUsername(self, username):
        cur, con = self._dbConnection()
        try:
            result = cur.execute(
                '''SELECT userId, username, accessLevel FROM tbl_Users WHERE LOWER(username) = LOWER(?)''',
                (username,)
            )
            result = result.fetchone()

            if result:
                return {
                    "successful": True,
                    "message": "User found.",
                    "errors": [],
                    "data": {
                        "userId": result[0],
                        "username": result[1],
                        "accessLevel": result[2]
                    },
                }
            return {
                "successful": False,
                "message": "User not found.",
                "errors": [],
            }
        except Exception as error:
            return {
                "successful": False,
                "message": "Error - user could not be found.",
                "errors": [str(error)]
            }
        finally:
            con.close()

    def getAllUsers(self):
        cur, con = self._dbConnection()
        try:
            result = cur.execute(
                '''SELECT userId, username, accessLevel FROM tbl_Users ORDER BY dateCreated DESC'''
            )
            result = result.fetchall()
            users = []
            for user in result:
                users.append({
                    'userId': user[0],
                    'username': user[1],
                    'accessLevel': user[2]
                })
            return {
                "successful": True,
                "message": "Users retrieved.",
                "errors": [],
                "data": users
            }
        finally:
            con.close()

    def deleteUser(self, username):
        cur, con = self._dbConnection()
        try:
            cur.execute(
                '''DELETE FROM tbl_Users WHERE username = ?''',
                (username,)
            )
            con.commit()
            return({
                "successful": True,
                "message": f"{username} was deleted successfully.",
                "errors": [],
                })
        except Exception as error:
            return {
                "successful": False,
                "message": f"Error trying to delete user.",
                "errors": [str(error)]
            }
        finally:
            con.close()
    
    def updateUser(self, username, newUsername=None, newPassword=None):
        if not self._userExists(username):
            return {
                "successful": False,
                "message": "User does not exist.",
                "errors": ["No user with username exists."]
            }
        if newUsername and self._userExists(newUsername):
            return {
                "successful": False,
                "message": 'This username already exists.',
                "errors": ["A user with the new username exists already."]
            }
        if newPassword:
            valid, errors = self._validatePassword(newPassword)
            if not valid:
                return {
                    "successful": False,
                    "message": "Password requirements have not been met.",
                    "errors": errors
                }
            
        cur, con = self._dbConnection()
        try:
            if newPassword:
                hashedPassword = self._hashPassword(newPassword)
                cur.execute(
                    '''UPDATE tbl_Users SET passwordHash = ? WHERE LOWER(username) = LOWER(?)''',
                    (hashedPassword, username)
                )
            if newUsername:
                cur.execute(
                    '''UPDATE tbl_Users SET username = ? WHERE LOWER(username) = LOWER(?)''',
                    (newUsername.lower(), username,)
                )
            con.commit()
            return {
                "successful": True,
                "message": "Successfully updated user.",
                "errors": []
            }
        except Exception as error:
            return {
                "successful": False,
                "message": "Error while updating user.",
                "errors": [str(error)]
            }
        finally:
            con.close()