import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

from core.config import FIREBASE_CREDENTIAL_PATH, FIREBASE_STORAGE_BUCKET

cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)
firebase_admin.initialize_app(cred, {
    'storageBucket': FIREBASE_STORAGE_BUCKET
})

db = firestore.client(database_id='splashbot-database')
bucket = storage.bucket()