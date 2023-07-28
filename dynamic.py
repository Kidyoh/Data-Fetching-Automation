import os
import requests
import pandas as pd
import urllib.parse
import xml.parsers.expat
import xmltodict
import json

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
    params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)

    country = params.get('country', 'Unknown')
    source = parsed.hostname
    datapoint = parsed.path.split('/')[-1]

    root_dir = 'data'
    source_dir = os.path.join(root_dir, source)
    country_dir = os.path.join(source_dir, country)
    datapoint_dir = os.path.join(country_dir, datapoint)
    os.makedirs(datapoint_dir, exist_ok=True)

    response = requests.get(url)

    if response.status_code == 200:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            data = response.json()
            with open(os.path.join(datapoint_dir, 'data.json'), 'w') as f:
                json.dump(data, f)

            # Flatten data and create DataFrame
            if isinstance(data, dict):
                flat_data = flatten_nested(data)
            else:
                flat_data = flatten_nested({"data": data})

            # Create DataFrame with each attribute-value pair in a separate row
            df_flat = pd.DataFrame(flat_data.items(), columns=['Attribute', 'Value'])

            # Save the flattened data to an Excel file
            file_path_flat = os.path.join(datapoint_dir, f"{datapoint}_flat.xlsx")
            df_flat.to_excel(file_path_flat, index=False)

            print("Flattened data saved to", file_path_flat)

        elif "application/xml" in content_type:
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

                # Convert XML to JSON
                json_data = xml_to_json(xml_data_cleaned)
                if json_data:
                    # Create DataFrame from JSON data
                    df_json = pd.read_json(json_data)

                    # Flatten data and create DataFrame with each attribute-value pair in a separate row
                    flat_data = flatten_nested(df_json)
                    df_flat = pd.DataFrame(flat_data.items(), columns=['Attribute', 'Value'])

                    # Save the flattened JSON data to an Excel file
                    file_path_excel = os.path.join(datapoint_dir, f"{datapoint}_cleaned.xlsx")
                    df_flat.to_excel(file_path_excel, index=False)

                    print(f'Cleaned JSON data saved to {file_path_excel}')
        else:
            print("Unsupported content type. Only JSON and XML are supported.")
