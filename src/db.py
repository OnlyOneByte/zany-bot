import sqlite3
from discord import User


DELETED_MSG_COLS = [
    'time',
    'react_message_id',
    'guild_id',
    'guild_name',
    'channel_id',
    'channel_name',
    'user_id',
    'user_name',
    'text',
    'attachments',
    'unlock_times'
    ]
DM_SCHEMA = {DELETED_MSG_COLS[i] : i for i in range(0, len(DELETED_MSG_COLS))}



def get_deleted_message(conn, reaction_id):
    sql = '''SELECT * FROM deleted_messages WHERE react_message_id=?'''
    return conn.execute(sql, (reaction_id,)).fetchone()


def add_deleted(conn, task):
    sql = f'INSERT INTO deleted_messages({",".join(DELETED_MSG_COLS)}) VALUES({",".join(["?"] * len(DELETED_MSG_COLS))})'
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()
    return

def add_user(conn, task):
    sql = '''INSERT INTO users(user_id,user_name,banked_zanycoins,robs_used)
              VALUES(?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, task)
    conn.commit()
    return

def check_user_bank(conn, user: User, cost: int, economyOptions):
    # Tries to take a zany coin away, if possible. If successful, return true, else false.
    # if user does not exist, it will create the user and continue.
    userRow = conn.execute("SELECT banked_zanycoins FROM users WHERE user_id=?", (user.id,)).fetchone()
    if userRow == None:
        # user does not exist, will create user and give him default number of items
        add_user(conn, (user.id, user.name, int(economyOptions['starting_amount'])), 0)
    user_coins = int(userRow[0]) if userRow else int(economyOptions['starting_amount'])
    if user_coins >= cost:
        conn.execute("UPDATE users SET banked_zanycoins=? WHERE user_id=?", (int(userRow[0])-cost, user.id))
        conn.commit()
        return True
    return False

def increment_unlock_times(conn, react_message_id, author_id):
    conn.execute("UPDATE deleted_messages SET unlock_times=unlock_times+? WHERE react_message_id=?", (1,react_message_id))
    conn.execute("UPDATE users SET banked_zanycoins=banked_zanycoins+? WHERE user_id=?", (1, author_id))
    conn.commit()

    
def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except sqlite3.Error as e:
        print(f"The error '{e}' occurred")

    if connection.execute("SELECT name FROM sqlite_master WHERE name='deleted_messages'").fetchone() is None:
        connection.execute(f"CREATE TABLE deleted_messages({','.join(DELETED_MSG_COLS)})")

    if connection.execute("SELECT name FROM sqlite_master WHERE name='users'").fetchone() is None:
        connection.execute("CREATE TABLE users(user_id,user_name,banked_zanycoins,robs_used)")
    connection.commit()
    return connection


