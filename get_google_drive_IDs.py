from os.path import exists
from dateutil import parser
import pandas as pd
from water_rights_visualizer.google_drive import google_drive_login

drive = google_drive_login()

landsat_directory_ID = "1HlxDjX2T-KPEG5UQyB8uHO_GFU-3sASi"
date_directory_listing = drive.ListFile(
    {'q': f"'{landsat_directory_ID}' in parents and trashed=false"}).GetList()

if exists("date_directory_IDs.csv"):
    date_directory_IDs = pd.read_csv("date_directory_IDs.csv")
else:
    date_directory_ID_rows = []

    for date_directory_item in date_directory_listing:
        datestamp = str(date_directory_item["title"])
        try:
            d = parser.parse(datestamp).date()
        except Exception as e:
            continue

        date_directory_ID = str(date_directory_item["id"])
        print(d, date_directory_ID)
        date_directory_ID_rows.append([d, date_directory_ID])

    date_directory_IDs = pd.DataFrame(
        date_directory_ID_rows, columns=["date", "ID"])

    date_directory_IDs.to_csv("date_directory_IDs.csv", index=False)

if exists("granule_directory_IDs.csv"):
    date_directory_IDs = pd.read_csv("granule_directory_IDs.csv")
else:
    granule_directory_ID_rows = []

    for i, (d, date_directory_ID) in date_directory_IDs.iterrows():
        if drive.auth.access_token_expired:
            drive.auth.Refresh()

        granule_directory_listing = drive.ListFile(
            {'q': f"'{date_directory_ID}' in parents and trashed=false"}).GetList()

        for granule_directory_item in granule_directory_listing:
            granule_ID = str(granule_directory_item["title"])
            granule_directory_ID = str(granule_directory_item["id"])
            print(granule_ID, granule_directory_ID)
            granule_directory_ID_rows.append(
                [d, granule_ID, granule_directory_ID])

    granule_directory_IDs = pd.DataFrame(granule_directory_ID_rows, columns=[
        "date", "granule_ID", "granule_directory_ID"])

    date_directory_IDs.to_csv("granule_directory_IDs.csv", index=False)

if exists("file_IDs.csv"):
    date_directory_IDs = pd.read_csv("file_IDs.csv")
else:
    file_ID_rows = []

    for i, (d, granule_ID, granule_directory_ID) in granule_directory_IDs.iterrows():
        if drive.auth.access_token_expired:
            drive.auth.Refresh()

        file_listing = drive.ListFile(
            {'q': f"'{granule_directory_ID}' in parents and trashed=false"}).GetList()

        for file_item in file_listing:
            filename = str(file_item["title"])
            file_ID = str(file_item["id"])
            print(filename, file_ID)
            file_ID_rows.append([d, granule_ID, filename, file_ID])

    file_IDs = pd.DataFrame(file_ID_rows, columns=[
                            "date", "granule_ID", "filename", "file_ID"])

    file_IDs.to_csv("file_IDs.csv", index=False)
