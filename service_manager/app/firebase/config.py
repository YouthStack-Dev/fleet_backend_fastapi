from dotenv import load_dotenv
load_dotenv()  # It will load .env file values into os.environ


import os
import firebase_admin
from firebase_admin import credentials, initialize_app, db

firebase_key_path = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_key_path)
        initialize_app(cred, {
            'databaseURL': 'https://ets-1-ccb71-default-rtdb.firebaseio.com/'
        })
