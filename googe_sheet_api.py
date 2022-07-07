import os.path
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SAMPLE_RANGE_NAME = 'Test List!A2:E246'

class GoogleSheet():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    service = None
    
    spreasheet_id = ""

    def __init__(self, sheet_id):
        creds = None

        self.spreasheet_id = sheet_id

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print('flow')
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        try:
            self.service = build('sheets', 'v4', credentials=creds)
        except:
            DISCOVERY_SERVICE_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
            self.service = build('sheets', 'v4', credentials=creds, discoveryServiceUrl=DISCOVERY_SERVICE_URL)

    def updateRangeValues(self, range, values):
        data = [{
            'range': range,
            'values': values
        }]
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }
        result = self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.spreasheet_id, body=body).execute()
#        print('{0} cells updated.'.format(result.get('totalUpdatedCells')))

    def clearSheet(self, g_range):
#        print(self.spreasheet_id, g_range)
        self.service.spreadsheets().values().clear(spreadsheetId=self.spreasheet_id, range=g_range, body={}).execute()
#        print('All cells cleared.')

