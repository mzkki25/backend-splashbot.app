from google.cloud import bigquery
from google.oauth2 import service_account

from core.config import GOOGLE_APPLICATION_CREDENTIALS, BIGQUERY_PROJECT_ID, BIGQUERY_DATASET_ID

import pandas as pd
import os

cred = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
client = bigquery.Client(credentials=cred, project=BIGQUERY_PROJECT_ID)

dataset_ref = client.dataset(BIGQUERY_DATASET_ID)