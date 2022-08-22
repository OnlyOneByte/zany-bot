import sqlite3
from discord import User

def get_deleted_message(conn, reaction_id):
    sql = '''SELECT * FROM deleted_messages WHERE react_message_id=?'''
    return conn.execute(sql, (reaction_id,)).fetchone()


def add_deleted(conn, task):
    sql = '''INSERT INTO deleted_messages(time,react_message_id,guild_id,channel_id,user_name,user_id,text,attachment_files)
              VALUES(?,?,?,?,?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()
    return

def add_user(conn, task):
    sql = '''INSERT INTO users(user_id,user_name,banked_zanycoins)
              VALUES(?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()
    return

def check_user_unlocks(conn, user: User, economyOptions):
    # Tries to take a zany coin away, if possible. If successful, return true, else false.
    # if user does not exist, it will create the user and continue.
    global CONFIG_OPTIONS
    userRow = conn.execute("SELECT banked_zanycoins FROM users WHERE user_id=?", (user.id,)).fetchone()
    if userRow == None:
        # user does not exist, will create user and give him default number of items
        add_user(conn, (user.id, user.name, economyOptions['starting_amount']-1))
        return True
    if int(userRow[0]) > 0:
        conn.execute("UPDATE users SET banked_zanycoins=? WHERE user_id=?", (int(userRow[0])-1, user.id))
        return True
    return False
    
    
def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except sqlite3.Error as e:
        print(f"The error '{e}' occurred")

    if connection.execute("SELECT name FROM sqlite_master WHERE name='deleted_messages'").fetchone() is None:
        connection.execute("CREATE TABLE deleted_messages(time,react_message_id,guild_id,channel_id,user_name,user_id,text,attachment_files)")

    if connection.execute("SELECT name FROM sqlite_master WHERE name='users'").fetchone() is None:
        connection.execute("CREATE TABLE users(user_id,user_name,banked_zanycoins)")
    
    return connection


