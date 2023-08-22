from flask import *
import urllib.parse
import os
import requests
import json, time
import pandas as pd
import xmltodict
import zipfile


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

def save_json_data(json_file, json_data):
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4)

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


def fetch_data_with_retry(url, max_retries=5, retry_delay=1, datapoint_dir=None):
    retry_count = 0
    while retry_count < max_retries:
        response = requests.get(url)
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                return response.json()
            elif "xml" in content_type:
                xml_data = response.text
                remove_invalid_characters(xml_data)
                save_xml_data(os.path.join(datapoint_dir, 'data.xml'), xml_data)
                json_data = xml_to_json(xml_data)
                return json_data
            else:
                print("Unsupported content type. Only JSON and XML responses are supported.")
                return None
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



# Flatten function
def flatten(d, parent_key=''):
  
  items = []
  
  if isinstance(d, dict):
    for k, v in d.items():
      new_key = f"{parent_key}_{k}" if parent_key else k   
      if isinstance(v, dict):
        items.extend(flatten(v, new_key).items())
      else:
        v = [v] # convert to list
        items.append((new_key, v))
        
  elif isinstance(d, list):
    for i, v in enumerate(d):
      new_key = f"{parent_key}_{i}"    
      if isinstance(v, dict):
        items.extend(flatten(v, new_key).items())
      else:
        v = [v] # convert to list
        items.append((new_key, v))

  return dict(items)


# Flatten data
def convert_to_excel(datapoint_dir,datapoint_name, country, data, flatten):
    

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



app = Flask(__name__, template_folder='.')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/requests/', methods=['GET'])
def requests_page():
    print(request.args)
    url = request.args.get('url')
    print("URL >> " + url)

    # Create directories
    datapoint_dir,country, datapoint_name = create_datapoint_dir(url)
    
    # Fetch data from API with retry handling
    data = fetch_data_with_retry(url)
    if data is None:
        return jsonify({'error': 'Failed to fetch data from the API.'}), 500

    # Dump data to json
    dumb_data_to_json(datapoint_dir, data)

    # Flatten Data
    flat_data = {}
    if isinstance(data, dict):
        flat_data = flatten(data)
    else:
        flat_data = flatten({"data": data})

    # convert to excel
    convert_to_excel(datapoint_dir,datapoint_name, country, data, flat_data)

    return datapoint_dir


if __name__ == '__main__':
    app.run(port=7777)