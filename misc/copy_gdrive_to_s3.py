from os import remove

import pandas as pd
import boto3
from water_rights_visualizer.google_drive import google_drive_login
import logging

logger = logging.getLogger(__name__)

drive = google_drive_login()
df = pd.read_csv("google_drive_file_IDs.csv")
# session = boto3.Session(profile_name="saml-pub")
session = boto3.Session()
s3 = session.resource("s3")
bucket = s3.Bucket("jpl-nmw-testbucket")

for i, (date,granule_ID,filename,file_ID,tile,variable) in df.iterrows():
    if not "012013" in filename:
        continue

    print(filename)

    try:
        google_drive_file = drive.CreateFile(metadata={"id": file_ID})
        google_drive_file.GetContentFile(filename=filename)
    except Exception as e:
        logger.exception(e)
        continue

    bucket.upload_file(filename, filename)
    remove(filename)
