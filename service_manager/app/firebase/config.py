import os
import firebase_admin
from firebase_admin import credentials, initialize_app, db

BASE_DIR = os.path.dirname(__file__)
cred_path = os.path.join(BASE_DIR, 'firebase_key.json')

def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        initialize_app(cred, {
            'databaseURL': 'https://ets-1-ccb71-default-rtdb.firebaseio.com/'
        })
