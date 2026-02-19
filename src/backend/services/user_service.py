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
            
        except sqlite3.Error as errorMessage:
            print(f"Error checking for username availability: {errorMessage}")
        finally:
            con.close()

    def createUser(self, username, password, accessLevel):
        if accessLevel not in ['ADMIN', 'MEMBER']:
            return {
                'successful': False,
                'errors': ['Invalid user access level.']
            }
        if self._userExists(username):
            return {
                'successful': False,
                'errors': ['This username already exists.']
            }
        valid, errors = self._validatePassword(password)
        if not valid:
            return {
                'successful': False,
                'errors': errors
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
                'successful': True,
                'errors': None
            }
        except sqlite3.Error as errorMessage:
            print(f"Error creating new user: {errorMessage}")
        finally:
            con.close()

    def authenticate(self, username, password):
        cur, con = self._dbConnection()
        try:
            result = cur.execute(
                '''SELECT userId, username, passwordHash, accessLevel FROM tbl_Users WHERE LOWER(username) = LOWER(?)''',
                (username,)
            )

            result = cur.fetchone()
            if not result:
                return {
                    'successful': False,
                    'errors': ['Username does not exist.'] 
                }
            
            db_userId, db_username, passwordHash, accessLevel = result
            ph = PasswordHasher()
            try:
                ph.verify(passwordHash, password)
                return {
                    'successful': True,
                    'userDetails': {
                        'userId': db_userId,
                        'username': db_username,
                        'accessLevel': accessLevel
                    }
                }
            except Exception:
                return {
                    'successful': False,
                    'errors': ['Username or password is invalid.', 'You can ask the admin to update your details or create a member account.']
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
                    'userId': result[0],
                    'username': result[1],
                    'accessLevel': result[2]
                }
            return None
        finally:
            con.close()

    def getAllUsers(self):
        cur, con = self._dbConnection()
        try:
            result = cur.execute(
                '''SELECT userId, username, accessLevel FROM tbl_Users ORDER BY dateCreated DESC'''
            )
            users = result.fetchall()
            users = []
            for user in users:
                users.append({
                    'userId': user[0],
                    'username': user[1],
                    'accessLevel': user[2]
                })
            return users
        finally:
            con.close()

    def deleteUser(self, username):
        cur, con = self._dbConnection()
        try:
            cur.execute(
                '''DELETE FROM tbl_Users WHERE username = ?''',
                (username,)
            )
            return({
                'successful': True,
                'errors': None
                })
        except sqlite3.Error as errorMessage:
            print(f"Error trying to delete user: {errorMessage}")
        finally:
            con.close()
    
    def updateUser(self, username, newUsername=None, newPassword=None):
        cur, con = self._dbConnection()
        try:
            if newPassword != None:
                valid, errors = self._validatePassword(newPassword)
                if not valid:
                    return {
                        'successful': False,
                        'errors': errors
                    }
                newPassword = self._hashPassword(newPassword)
                cur.execute(
                    '''UPDATE tbl_Users SET passwordHash = ? WHERE LOWER(username) = LOWER(?)''',
                    (newPassword, username)
                )
                con.commit()

            if newUsername != None:
                if self._userExists(newUsername):
                    return {
                        'successful': False,
                        'errors': ['This username already exists.']
                    }
                cur.execute(
                    '''UPDATE tbl_Users SET username = ? WHERE LOWER(username) = LOWER(?)''',
                    (newUsername, username,)
                )
                con.commit()
            return {
                'successful': True,
                'errors': None
            }
        except sqlite3.Error as errorMessage:
            print(f"Error while updating user's username: {errorMessage}")
            return {
                'successful': False,
                'errors': ['Error occurred while updating the user\'s username.']
            }
        finally:
            con.close()