import os
import requests
import pandas as pd
import urllib.parse
from aspose.cells import Workbook
from msal import ConfidentialClientApplication

# Define the Microsoft Graph API endpoints
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
DRIVE_BASE_URL = f"{GRAPH_BASE_URL}/me/drive"

# Read Excel file
df = pd.read_excel('indicators.xlsx')

indicators = df['Indicator'].tolist()

# Set country to Ethiopia
country = 'ETH'

# Create a workbook to save data
workbook = Workbook()

# Insert your Microsoft Graph API credentials here
client_id = "8c31f0a0-26ca-42d2-99fd-e2d8d2a6b08d"
client_secret = "ULy8Q~Amcjr0_MaIfEZqhbVfRZUiPUA1Zg4QhbBV"
tenant_id = "f8cdef31-a31e-4b4a-93e4-5f571e91255a"

# Create a ConfidentialClientApplication object for authentication
app = ConfidentialClientApplication(
    client_id=client_id,
    client_credential=client_secret,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
)

# Function to get an access token for OneDrive
def get_access_token():
    scope = ["https://graph.microsoft.com/.default"]
    result = app.acquire_token_silent(scope, account=None)

    if not result:
        result = app.acquire_token_for_client(scopes=scope)

    if "access_token" in result:
        return result["access_token"]
    else:
        raise ValueError("Failed to obtain access token.")

# Function to upload a file to OneDrive
def upload_to_onedrive(file_path, folder_id):
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    upload_url = f"{DRIVE_BASE_URL}/items/{folder_id}:/{os.path.basename(file_path)}:/content"
    with open(file_path, "rb") as f:
        response = requests.put(upload_url, data=f, headers=headers)
        if response.status_code == 200:
            print(f"File uploaded to OneDrive: {file_path}")
        else:
            print(f"Failed to upload file: {file_path}")

for indicator in indicators:
    url = f"https://api.worldbank.org/countries/{country}/indicators/{indicator}"
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    source = parsed.hostname  # worldbank.org
    datapoint = parsed.path.split('/')[-1]  # population
    root_dir = 'data'
    source_dir = os.path.join(root_dir, source)
    country_dir = os.path.join(source_dir, country)
    datapoint_dir = os.path.join(country_dir, datapoint)
    os.makedirs(datapoint_dir, exist_ok=True)
    # Make API request
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(datapoint_dir, f'{datapoint}.xml'), 'w') as f:
            f.write(response.text)
        # Upload the file to OneDrive
        upload_to_onedrive(
            os.path.join(datapoint_dir, f'{datapoint}.xml'), "A57172FE32FAC5C3%21687"
        )

    print('Data saved to worksheet', indicator)

# Save the entire workbook to the Excel file
workbook.save("Output.xlsx")
print('Excel file "Output.xlsx" saved.')
