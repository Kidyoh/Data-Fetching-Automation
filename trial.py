import os
import requests
import pandas as pd
import urllib.parse
import xml.parsers.expat
import xmltodict
from aspose.cells import Workbook
from openpyxl import Workbook

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

def extract_data_from_xml(xml_data):
    data = []
    try:
        xml_dict = xmltodict.parse(xml_data)
        indicators = xml_dict.get('Indicators', {}).get('Indicator', [])
        if not isinstance(indicators, list):
            indicators = [indicators]  # Handle the case when only one indicator is present
        for indicator in indicators:
            date = indicator.get('@Date')
            value = indicator.get('@Value')
            name = indicator.get('@Name')
            data.append({'Date': date, 'Value': value, 'Indicator': name})
    except xml.parsers.expat.ExpatError:
        print("Error parsing XML data.")
    return data

if __name__ == "__main__":
    url = input("Enter API URL: ")

    parsed = urllib.parse.urlparse(url)
    source = parsed.hostname  
    datapoint = parsed.path.split('/')[-1]
    root_dir = 'data'
    source_dir = os.path.join(root_dir, source)
    datapoint_dir = os.path.join(source_dir, datapoint)
    os.makedirs(datapoint_dir, exist_ok=True)

    # Make API request
    response = requests.get(url)
    print(response.status_code)
    if response.status_code == 200:
        content_type = response.headers.get("content-type", "")
        print(content_type)

        xml_data = response.text
        # Remove characters before <?xml version declaration
        xml_data_cleaned = remove_invalid_characters(xml_data)
        if xml_data_cleaned:
            # Save the cleaned XML data to the file (ensure well-formed XML)
            xml_file = os.path.join(datapoint_dir, f'{datapoint}.xml')
            save_xml_data(xml_file, xml_data_cleaned)

            print(f'Cleaned XML data saved to {xml_file}')

            # Extract data from XML
            data = extract_data_from_xml(xml_data_cleaned)

            # Convert data to DataFrame
            df_xml = pd.DataFrame(data)

            # Save the cleaned XML data to an Excel file
            file_path_excel = os.path.join(datapoint_dir, f"{datapoint}_cleaned.xlsx")
            df_xml.to_excel(file_path_excel, index=False)

            print(f'Cleaned XML data saved to {file_path_excel}')
        else:
            print("Unsupported content type. Only XML responses are supported.")

    else:
        print("Failed to fetch data from the API.")
