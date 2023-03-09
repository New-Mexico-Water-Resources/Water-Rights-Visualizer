from os import remove

import pandas as pd
import boto3
from water_rights_visualizer.google_drive import google_drive_login

drive = google_drive_login()
df = pd.read_csv("google_drive_file_IDs.csv")
session = boto3.Session(profile_name="saml-pub")
s3 = session.resource("s3")
bucket = s3.Bucket("jpl-nmw-testbucket")

for i, (date,granule_ID,filename,file_ID,tile,variable) in df.iterrows():
    print(filename)
    google_drive_file = drive.CreateFile(metadata={"id": file_ID})
    google_drive_file.GetContentFile(filename=filename)
    bucket.upload_file(filename, filename)
    remove(filename)
