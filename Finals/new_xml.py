from flask import *
import os
import requests
import pandas as pd
import urllib.parse
import xml.parsers.expat
import xmltodict
import time

import json


app = Flask(__name__)

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
def create_datapoint_dir(url):
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)

    country = params.get('country', 'unknown')[0]
    source = parsed.hostname  # worldbank.org
    datapoint_name = parsed.path.split('/')[-1]  # population

    root_dir = 'data'
    source_dir = os.path.join(root_dir, source)
    country_dir = os.path.join(source_dir, country)
    datapoint_dir = os.path.join(country_dir, datapoint_name)

    os.makedirs(datapoint_dir, exist_ok=True)

    return datapoint_dir, country, datapoint_name


def fetch_data_with_retry(url, max_retries=5, retry_delay=1):
    retry_count = 0
    while retry_count < max_retries:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_count += 1
            print(f"Rate limit exceeded. Retry attempt {retry_count} in {retry_delay} second.")
            time.sleep(retry_delay)
        else:
            print(f"Failed to fetch data from the API. Status code: {response.status_code}")
            return None

    print(f"Max retries reached. Unable to fetch data from the API.")
    return None


def dumb_data_to_json(datapoint_dir, data):
    with open(os.path.join(datapoint_dir, 'data.json'), 'w') as f:
        json.dump(data, f)
# Function to convert API response to Excel (both JSON and XML)
def convert_to_excel(datapoint_dir, datapoint_name, country, data, response_type, flatten):
    if response_type == "json":
         # Create DataFrame from the flattened data
      df_flat = pd.DataFrame.from_dict(flatten)
  
  # Save the flattened data to an Excel file
      file_path_flat = os.path.join(datapoint_dir, f"{datapoint_name}_flat.xlsx")
      df_flat.to_excel(file_path_flat, index=False)
  
      print("Flattened data saved to", file_path_flat)
  
# Create separate DataFrames for each country
      dfs_by_country = {}
      if isinstance(data, dict):
          for country_code, country_data in data.items():
              df = pd.json_normalize(country_data, meta='all')
              dfs_by_country[country_code] = df
      else:
          df = pd.json_normalize(data, meta='all')
          dfs_by_country[country] = df
  
# Save each DataFrame to a separate sheet in the Excel file
      with pd.ExcelWriter(os.path.join(datapoint_dir, f"{datapoint_name}_of_{country}.xlsx")) as writer:
          for country_code, df in dfs_by_country.items():
              df.to_excel(writer, sheet_name=country_code, index=False)
  
      print("Data saved by country to", os.path.join(datapoint_dir, f"{datapoint_name}_of_{country}.xlsx"))
  
    elif response_type == "xml":
        xml_data = response_type.text
            # Remove characters before <?xml version declaration
        delay_between_requests = 0
        xml_data_cleaned = remove_invalid_characters(xml_data)
        if xml_data_cleaned:
                    # Save the cleaned XML data to the file (ensure well-formed XML)
                    xml_to_json(xml_data_cleaned)
                    json_file = os.path.join(datapoint_dir, f'{datapoint_name}.json')
                    xml_file = os.path.join(datapoint_dir, f'{datapoint_name}.xml')
                    save_xml_data(xml_file, xml_data_cleaned)
       
                    print(f'Cleaned XML data saved to {xml_file}')
       
                    # Save the cleaned XML data to an Excel file
                    file_path_excel = os.path.join(datapoint_dir, f"{datapoint_name}_cleaned.xlsx")
                    df_xml = pd.read_xml(xml_file)
                    df_xml.to_excel(file_path_excel, index=False)
       
                    print(f'Cleaned XML data saved to {file_path_excel}')
        else:
                print("Unsupported content type. Only XML responses are supported.")
       
    else:
        print("Failed to fetch data from the API.")
        time.sleep(delay_between_requests)

@app.route('/process_apis/', methods=['GET'])
def process_apis():
    api_urls = []
    with open('Finals/api_urls.txt', 'r') as f:
        api_urls = f.read().splitlines()

    for url in api_urls:
        print("URL >> " + url)

        # Create directories
        datapoint_dir, country, datapoint_name = create_datapoint_dir(url)

        # Fetch data from API with retry handling
        data = fetch_data_with_retry(url)
        if data is None:
            return jsonify({'error': 'Failed to fetch data from the API.'}), 500

        # Determine the response type based on the URL
        if "json" in url:
            response_type = "json"
        elif "xml" in url:
            response_type = "xml"
        else:
            return jsonify({'error': 'Unsupported content type.'}), 400

        # Dump data to JSON
        dumb_data_to_json(datapoint_dir, data)

        # Convert to Excel
        convert_to_excel(datapoint_dir, datapoint_name, country, data, response_type)

    return jsonify({'message': 'APIs processed successfully.'})

if __name__ == '__main__':
    app.run(port=7777)