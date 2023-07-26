import os
import requests
import pandas as pd
import urllib.parse
from aspose.cells import Cells
from aspose.cells import Workbook
import re



# Read Excel file
df = pd.read_excel('indicators.xlsx')

indicators = df['Indicator'].tolist()


# Set country to Ethiopia
country = 'ETH'

# Create a workbook to save data
workbook = Workbook()

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

    with open(os.path.join(datapoint_dir, f'{datapoint}.xml'), 'w') as f:
        f.write(response.text)

    print('Data saved to worksheet', indicator)
# Save the entire workbook to the Excel file
workbook.save("Output.xlsx")
print('Excel file "Output.xlsx" saved.')
