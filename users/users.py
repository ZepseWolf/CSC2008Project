import sqlite3

# USER
def create_user(db, username, email, name, password) -> bool:
    try:
        db.execute("INSERT INTO Users (username, email, name, password) VALUES (?, ?, ?, ?)", (username, email, name, password,))
        db.commit()
        return True
    except:
        return False
    
def delete_user(db, username) -> bool:
    try:
        db.execute("DELETE FROM Users WHERE username = ?", (username,))
        db.commit()
        return True
    except:
        return False
    
def update_user(db, username, email, name, password) -> bool:
    try:
        db.execute("UPDATE Users SET email=?, name=?, password=? WHERE username=?", (email, name, password, username,))
        db.commit()
        return True
    except:
        return False
    
def get_user(db, username):
    try:
        data = db.execute("SELECT * FROM Users WHERE username=?", (username,)).fetchone()
        return data
    except:
        return None

def check_credentials(db, username, password) -> bool:
    try:
        db.execute("SELECT * FROM Users WHERE username=? AND password=?", (username, password,)).fetchone()
        return True
    except:
        return False
    

# DIGIMON TEAM 
def create_team(db, username, digimon_1, digimon_2, digimon_3, digimon_4, digimon_5, digimon_6) -> bool:
    try:
        db.execute("INSERT INTO User_Digimon (username, digimon_1, digimon_2, digimon_3, digimon_4, digimon_5, digimon_6) VALUES (?, ?, ?, ?, ?, ?, ?)", (username, digimon_1, digimon_2, digimon_3, digimon_4, digimon_5, digimon_6,))
        db.commit()
        return True
    except:
        return False
    
def get_team(db, username):
    try:
        data = db.execute("SELECT * FROM User_Digimon WHERE username=?", (username,)).fetchone()
        return data
    except:
        return None
    
def delete_team(db, username) -> bool:
    try:
        db.execute("DELETE FROM User_Digimon WHERE username=?", (username,))
        db.commit()
        return True
    except:
        return False
    
def update_team(db, username, digimon_1, digimon_2, digimon_3, digimon_4, digimon_5, digimon_6) -> bool:
    try:
        db.execute("UPDATE User_Digimon SET digimon_1=?, digimon_2=?, digimon_3=?, digimon_4=?, digimon_5=?, digimon_6=? WHERE username=?", (digimon_1, digimon_2, digimon_3, digimon_4, digimon_5, digimon_6, username,))
        db.commit()
        return True
    except:
        return False

def get_all_digimons(db):
    try:
        data = db.execute("SELECT digimon_name, stage, digimon_type, attribute FROM DIGIMON").fetchall()
        return data
    except:
        return None
