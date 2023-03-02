import sys
from os import makedirs
from os.path import join, abspath, dirname, exists
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

KEY_FILENAME = join(abspath(dirname(__file__)), "google_drive_key.txt")
# KEY_FILENAME = join("~", ".water_rights", "google_drive_key.txt")

def google_drive_login(key_filename: str = None) -> GoogleDrive:
    if key_filename is None:
        key_filename = KEY_FILENAME

    gauth = GoogleAuth()
    # Try to load saved client credentials
    gauth.settings["get_refresh_token"] = True

    print(f"loading credentials: {key_filename}")
    gauth.LoadCredentialsFile(key_filename)

    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.GetFlow()
        gauth.flow.params.update({'access_type': 'offline'})
        gauth.flow.params.update({'approval_prompt': 'force'})
        gauth.LocalWebserverAuth()
        # gauth.CommandLineAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    makedirs(dirname(key_filename), exist_ok=True)
    print(f"saving credentials: {key_filename}")
    gauth.SaveCredentialsFile(key_filename)
    drive = GoogleDrive(gauth)

    return drive
