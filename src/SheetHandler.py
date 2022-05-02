import os
from googleapiclient.discovery import build 
from google.oauth2 import service_account


class SheetHandler:
    def __init__(self, logger):
        self.logger = logger
        self.scope = ['https://www.googleapis.com/auth/spreadsheets']
        self.spreadsheet_id = os.environ["SPREADSHEET_ID"]
        self.credentials = service_account.Credentials.from_service_account_file('credentials.json', scopes=self.scope)
        self.spreadsheet = build('sheets', 'v4', credentials=self.credentials)

    def add_new_record(self, name, rarity, type, id, condition, jpy_price, thb_price):
        range = "Sheet1!A:F"
        rows = [
            [name, rarity, type, id, condition, jpy_price, thb_price]
        ]
        body = {
            'majorDimension': 'ROWS',
            'values': rows
        }

        result = self.spreadsheet.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id, range=range, body=body, valueInputOption="USER_ENTERED"
            ).execute()

        self.logger.info("SheetHandler.add_new_record", "{0} row added".format(result["updates"]["updatedRows"]))
