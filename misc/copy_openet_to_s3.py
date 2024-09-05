from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from tqdm import tqdm
import boto3
import os

gauth = GoogleAuth()

gauth.LoadCredentialsFile("water_rights_gdrive_creds.txt")
if gauth.credentials is None:
    # gauth.CommandLineAuth()
    gauth.LocalWebserverAuth(port_numbers=[8091])
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()

gauth.SaveCredentialsFile("water_rights_gdrive_creds.txt")

drive = GoogleDrive(gauth)

session = boto3.Session()
s3 = session.resource("s3")
bucket = s3.Bucket("ose-dev-inputs")

monthly_folder = drive.ListFile({"q": "title='OpenET Data' and trashed=false"}).GetList()
monthly_files = drive.ListFile({"q": f"'{monthly_folder[0]['id']}' in parents and trashed=false"}).GetList()
pbar = tqdm(monthly_files)
for file in pbar:
    pbar.set_description(f"{file['title']}")
    if drive.auth.access_token_expired:
        drive.auth.Refresh()

    filename = file["title"]
    file.GetContentFile(filename)

    bucket.upload_file(filename, filename)

    # Delete the file after uploading
    os.remove(filename)
