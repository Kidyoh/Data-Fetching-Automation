import os
import requests 
import pandas as pd
from urllib.parse import urlparse
import json
import xml.etree.ElementTree as ET
from urllib.parse import parse_qsl


# Parse URL 
def parse_url(url):
    parsed = urlparse(url)
    params = dict(parse_qsl(parsed.query))
    
    country = params.get('country', 'unknown')
    source = parsed.hostname
    datapoint = parsed.path.split('/')[-1]
    
    return country, source, datapoint

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

# Create directory
def create_dir(root, source, country, datapoint):
    source_dir = os.path.join(root, source) 
    os.makedirs(source_dir, exist_ok=True)

    country_dir = os.path.join(source_dir, country)
    os.makedirs(country_dir, exist_ok=True)

    datapoint_dir = os.path.join(country_dir, datapoint)
    os.makedirs(datapoint_dir, exist_ok=True)
    
    return datapoint_dir


# Flatten data
def convert_to_excel(datapoint_dir,datapoint_name, flatten):
    

# Create DataFrame from the flattened data
    df_flat = pd.DataFrame.from_dict(flatten)

# Save the flattened data to an Excel file
    file_path_flat = os.path.join(datapoint_dir, f"{datapoint_name}_flat.xlsx")
    df_flat.to_excel(file_path_flat, index=False)

    print("Flattened data saved to", file_path_flat)



#flatten function
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

#Dumping data to JSON
def dumb_data_to_json(datapoint_dir, data):
  with open(os.path.join(datapoint_dir, 'data.json'), 'w') as f:
      json.dump(data, f)

# Process API response
def process_response(response, datapoint_dir, datapoint):
    if response.status_code == 200:
        content_type = response.headers.get("Content-Type")
        
        if "application/json" in content_type:
            data = response.json()
            dumb_data_to_json(datapoint_dir, data)
            data = {k: [v] for k, v in data.items()}
            df = pd.DataFrame(data)

            excel_file = os.path.join(datapoint_dir, f"{datapoint}.xlsx")
            df.to_excel(excel_file, index=False)
            print("Saved to Excel:", excel_file)

            
        elif "application/xml" in content_type or "text/xml" in content_type:
            xml_data = response.text
            xml = remove_invalid_characters(xml_data)
            xml_file = os.path.join(datapoint_dir, f"{datapoint}.xml")
            save_xml_data(xml_file, xml)

            print(f'Cleaned XML data saved to {xml_file}')

            file_path_excel = os.path.join(datapoint_dir, f"{datapoint}_cleaned.xlsx")
            df_xml = pd.read_xml(xml_file)
            df_xml.to_excel(file_path_excel, index=False)
            print(f'Cleaned XML data saved to {file_path_excel}')
            
            
        else:
            print("Unsupported content type:", content_type)
            return
        
        

    else:
        print("Request failed with status code:", response.status_code)
        
# Main function        
def main():
    root_dir = 'data'
    
    with open(r'C:\Users\J\Downloads\AutomatedDataCollectionApi\AutomatedDataCollectionApi\AutomatedDataCollectionApi\Services\apis_parsed.txt') as f:

        urls = f.readlines()
        
    for url in urls:
        url = url.strip()
        country, source, datapoint = parse_url(url)
        datapoint_dir = create_dir(root_dir, source, country, datapoint)
        
        response = requests.get(url)
        process_response(response, datapoint_dir, datapoint)
        
if __name__ == '__main__':
    main()