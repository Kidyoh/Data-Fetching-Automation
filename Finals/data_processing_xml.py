import os
import requests
import pandas as pd
import urllib.parse
import xml.parsers.expat
import xmltodict
from aspose.cells import Workbook
from openpyxl import Workbook
import time

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


def xml_to_json(xml_data):
    return xmltodict.parse(xml_data)

if __name__ == "__main__":
    api_file = "Finals/api_urls.txt"
    indicator_mapping_file = "Finals/indicator_mapping.xlsx"

    indicator_mapping_df = pd.read_excel(indicator_mapping_file)
    indicator_mapping = dict(zip(indicator_mapping_df['INDICATOR_CODE'], indicator_mapping_df['INDICATOR_NAME']))
    with open(api_file, "r") as f:
        api_urls = f.readlines()

    delay_between_requests = 0
    processed_indicators = set()  # Keep track of processed indicators
    processed_urls = [] 

    for url in api_urls:
        url = url.strip() # Remove newline characters
        if url in processed_urls:
         print(f"URL {url} already processed. Skipping...")
         continue

        parsed = urllib.parse.urlparse(url)
        source = parsed.hostname
        country = 'ETH'
        datapoint = parsed.path.split('/')[-1]
        root_dir = 'data'
        source_dir = os.path.join(root_dir, source)
        country_dir = os.path.join(source_dir,country)
        datapoint_dir = os.path.join(country_dir, datapoint)
        os.makedirs(datapoint_dir, exist_ok=True)

        # Check if indicator was already processed
        if datapoint in processed_indicators:
            print(f"Indicator '{datapoint}' already processed. Skipping...")
            continue

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
                    xml_to_json(xml_data_cleaned)
                    json_file = os.path.join(datapoint_dir, f'{datapoint}.json')
                    xml_file = os.path.join(datapoint_dir, f'{datapoint}.xml')
                    save_xml_data(xml_file, xml_data_cleaned)
       
                    print(f'Cleaned XML data saved to {xml_file}')
       
                    # Save the cleaned XML data to an Excel file
                    file_path_excel = os.path.join(datapoint_dir, f"{datapoint}_cleaned.xlsx")
                    df_xml = pd.read_xml(xml_file)
                    df_xml.to_excel(file_path_excel, index=False)
       
                    print(f'Cleaned XML data saved to {file_path_excel}')
            else:
                print("Unsupported content type. Only XML responses are supported.")
       
        else:
            print("Failed to fetch data from the API.")
        time.sleep(delay_between_requests)