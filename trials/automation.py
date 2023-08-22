import os
import requests
import pandas as pd
import xmltodict
import json
import xml.parsers.expat
import urllib.parse

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

# Function to convert XML to JSON
def xml_to_json(xml_string):
    try:
        data_dict = xmltodict.parse(xml_string)
        json_data = json.dumps(data_dict)
        return json_data
    except xml.parsers.expat.ExpatError as e:
        print(f"Error parsing XML: {e}")
        return None

def save_xml_data(xml_file, xml_data):
    with open(xml_file, "w", encoding="utf-8") as f:
        f.write(xml_data)

def flatten_nested(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_nested(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

if __name__ == "__main__":
    url = input("Enter API URL: ")

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    country = params.get('country', 'Unknown')
    source = parsed.hostname
    datapoint = parsed.path.split('/')[-1]

    root_dir = 'data'
    source_dir = os.path.join(root_dir, source)
    country_dir = os.path.join(source_dir, country)
    os.makedirs(country_dir, exist_ok=True)

    datapoint_dir = os.path.join(country_dir, datapoint)
    os.makedirs(datapoint_dir, exist_ok=True)

    # Send request to the API
    response = requests.get(url)

    if response.status_code == 200:
        content_type = response.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            # Parse JSON data
            data = response.json()

            # Flatten data and create DataFrame
            flat_data = flatten_nested(data)
            df_flat = pd.DataFrame(flat_data.items(), columns=['Attribute', 'Value'])

            # Create folders based on the provided structure
            

            # Save the flattened data to an Excel file within the specified folder
            file_path_flat = os.path.join(datapoint_dir, f"{datapoint}_flat.xlsx")
            df_flat.to_excel(file_path_flat, index=False)

            print("Flattened data saved to", file_path_flat)

        elif "application/xml" in content_type:
            # Process XML data
            xml_data = response.text

            # Remove characters before <?xml version declaration
            xml_data_cleaned = remove_invalid_characters(xml_data)
            if xml_data_cleaned:
                # Save the cleaned XML data to the file (ensure well-formed XML)
                xml_file = os.path.join(datapoint_dir, f'{datapoint}.xml')
                save_xml_data(xml_file, xml_data_cleaned)

                # Convert XML to JSON
                json_data = xml_to_json(xml_data_cleaned)
                if json_data:
                    # Parse JSON data
                    data = json.loads(json_data)

                    # Flatten data and create DataFrame
                    flat_data = flatten_nested(data)
                    df_flat = pd.DataFrame(flat_data.items(), columns=['Attribute', 'Value'])

                    # Save the flattened data to an Excel file within the specified folder
                    file_path_flat = os.path.join(datapoint_dir, f"{datapoint}_flat.xlsx")
                    df_flat.to_excel(file_path_flat, index=False)

                    print("Flattened data saved to", file_path_flat)
                else:
                    print("Error converting XML to JSON.")
        else:
            print("Unsupported content type. Only JSON and XML are supported.")
    else:
        print("Error fetching data from the API.")
