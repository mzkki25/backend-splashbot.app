import os
import dotenv

dotenv.load_dotenv()

GCS_API_KEY = os.getenv("GCS_API_KEY")
GCS_CX = os.getenv("GCS_CX")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

FIREBASE_CREDENTIAL_PATH = "helper/credentials.json"
FIREBASE_STORAGE_BUCKET = "adi-internship-2.firebasestorage.app"
GOOGLE_APPLICATION_CREDENTIALS = "helper/credentials.json"
BIGQUERY_PROJECT_ID = ""
BIGQUERY_DATASET_ID = ""