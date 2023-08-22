import os
import requests
import pandas as pd
import urllib.parse
import xml.parsers.expat
import xmltodict
from aspose.cells import Workbook

# Function to remove characters before the <?xml version declaration
def remove_invalid_characters(xml_data):
    xml_declaration = '<?xml version'
    start_index = xml_data.find(xml_declaration)
    if start_index != -1:
        cleaned_data = xml_data[start_index:]
        return cleaned_data
    else:
        print("Invalid XML data format.")
        return None

def save_xml_data(xml_file, xml_data):
    with open(xml_file, "w", encoding="utf-8") as f:
        f.write(xml_data)

if __name__ == "__main__":
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
        if response.status_code == 200:
            xml_data = response.text
            # Remove characters before <?xml version declaration
            xml_data_cleaned = remove_invalid_characters(xml_data)
            if xml_data_cleaned:
                # Save the cleaned XML data to the file (ensure well-formed XML)
                xml_file = os.path.join(datapoint_dir, f'{datapoint}.xml')
                save_xml_data(xml_file, xml_data_cleaned)

                # Save the cleaned XML data to an Excel file
                file_path_xml = os.path.join(datapoint_dir, f"{datapoint}_cleaned.xml")
                with open(file_path_xml, "w", encoding="utf-8") as f:
                    f.write(xml_data_cleaned)

                print(f'Cleaned XML data saved to {file_path_xml}')

                # Save the cleaned XML data to an Excel file
                file_path_excel = os.path.join(datapoint_dir, f"{datapoint}_cleaned.xlsx")
                df_xml = pd.read_xml(file_path_xml)
                df_xml.to_excel(file_path_excel, index=False)

                print(f'Cleaned XML data saved to {file_path_excel}')

    # Save the entire workbook to the Excel file
    workbook.save("Output.xlsx")
    print('Excel file "Output.xlsx" saved.')
