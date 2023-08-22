import main
import sqlite3
import json
import os

DATABASE = 'tokens.db'

def get_token_from_sqlite():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT token FROM tokens ORDER BY id DESC LIMIT 1")
    token = c.fetchone()
    conn.close()
    if token:
        return token[0]
    return None

def save_token_to_sqlite(j_token):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO tokens (token) VALUES (?)", (j_token,))
    conn.commit()
    conn.close()

def get_day_count():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS post_count (id INTEGER PRIMARY KEY, day_count INTEGER)")
    c.execute("SELECT day_count FROM post_count ORDER BY id DESC LIMIT 1")
    count = c.fetchone()
    conn.close()
    if count:
        return count[0]
    else:
        set_day_count(1)
        return 1

def increment_day_count():
    current_count = get_day_count()
    new_count = current_count + 1
    set_day_count(new_count)

def set_day_count(count):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO post_count (day_count) VALUES (?)", (count,))
    conn.commit()
    conn.close()

x = main.make_token()
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
token_url = "https://api.twitter.com/2/oauth2/token"

token = get_token_from_sqlite()
bb_t = token.replace("'", '"')
data = json.loads(bb_t)

refreshed_token = x.refresh_token(
    client_id=client_id,
    client_secret=client_secret,
    token_url=token_url,
    refresh_token=data["refresh_token"],
)

t_refreshed_token = '"{}"'.format(refreshed_token)
j_refreshed_token = json.loads(t_refreshed_token)
save_token_to_sqlite(j_refreshed_token)

day_count = get_day_count()
unban_shkreli = f"@elonmusk - Attempt #{day_count} of posting 'till @martinshkreli is unbanned"
payload = {"text": unban_shkreli}
main.make_post(payload, refreshed_token)
increment_day_count()
