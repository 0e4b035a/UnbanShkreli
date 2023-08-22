import base64
import hashlib
import os
import re
import json
import requests
import sqlite3
from requests.auth import AuthBase, HTTPBasicAuth
from requests_oauthlib import OAuth2Session, TokenUpdated
from flask import Flask, request, redirect, session, url_for, render_template
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = 'application.log'

# Set up a rotating log handler (max 2 log files, each up to 1MB in size)
file_handler = RotatingFileHandler(log_file, maxBytes=1*1024*1024, backupCount=2)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(50)

client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
redirect_uri = os.environ.get("REDIRECT_URI")
auth_url = "https://twitter.com/i/oauth2/authorize"
token_url = "https://api.twitter.com/2/oauth2/token"

scopes = ["tweet.read", "users.read", "tweet.write", "offline.access"]

DATABASE = 'tokens.db'
conn = sqlite3.connect(DATABASE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS tokens (id INTEGER PRIMARY KEY, token TEXT)''')
conn.commit()
conn.close()

code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)

code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
code_challenge = code_challenge.replace("=", "")

def make_token():
    return OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scopes)

def make_post(payload, token):
    app.logger.info("Posting on X!")
    response = requests.request(
        "POST",
        "https://api.twitter.com/2/tweets",
        json=payload,
        headers={
            "Authorization": "Bearer {}".format(token["access_token"]),
            "Content-Type": "application/json",
        },
    )
    
    # Check if the response was successful
    if 200 <= response.status_code < 300:
        app.logger.info(f"Successfully posted! Status code: {response.status_code}")
    else:
        app.logger.error(f"Failed to post. Status code: {response.status_code}, Response: {response.text}")

    return response

@app.route("/")
def auth():
    global twitter
    twitter = make_token()
    authorization_url, state = twitter.authorization_url(
        auth_url, code_challenge=code_challenge, code_challenge_method="S256"
    )
    session["oauth_state"] = state
    return redirect(authorization_url)

@app.route("/oauth/callback", methods=["GET"])
def callback():
    code = request.args.get("code")
    token = twitter.fetch_token(
        token_url=token_url,
        client_secret=client_secret,
        code_verifier=code_verifier,
        code=code,
    )
    st_token = '"{}"'.format(token)
    j_token = json.loads(st_token)
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO tokens (token) VALUES (?)", (j_token,))
    conn.commit()
    conn.close()
    
    unban_shkreli = "@elonmusk everyday 'till we get the bag from Shkreli!" 
    payload = {"text": "{}".format(unban_shkreli)}
    response = make_post(payload, token).json()
    return response

if __name__ == "__main__":
    app.run()
