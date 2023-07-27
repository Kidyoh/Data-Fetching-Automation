import os
import requests
import pandas as pd
import urllib.parse
import xml.parsers.expat
import xmltodict
from aspose.cells import Workbook
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

                # Convert XML to JSON
                json_data = xml_to_json(xml_data_cleaned)
                if json_data:
                    # Create DataFrame from JSON data
                    df_json = pd.read_json(json_data)

                    # Save the JSON data to an Excel file in a separate sheet for each country
                    sheet_name = f"{country}_{datapoint}"
                    file_path_json = os.path.join(datapoint_dir, f"{datapoint}.xlsx")
                    with pd.ExcelWriter(file_path_json, engine='xlsxwriter') as writer:
                        df_json.to_excel(writer, sheet_name=sheet_name, index=False)
                        worksheet = writer.sheets[sheet_name]
                        worksheet.autofilter(0, 0, df_json.shape[0], df_json.shape[1] - 1)  # Add autofilter
                        worksheet.freeze_panes(1, 0)  # Freeze the top row
                        worksheet.set_column('A:A', 30)  # Adjust column width

                    print(f'JSON data saved to {file_path_json}')

                    # Flatten data
                    if isinstance(df_json, dict):
                        flat_data = flatten(df_json)
                    else:
                        flat_data = flatten({"data": df_json})

                    # Create DataFrame from the flattened data
                    df_flat = pd.DataFrame.from_dict(flat_data)

                    # Save the flattened data to an Excel file
                    file_path_flat = os.path.join(datapoint_dir, f"{datapoint}_flat.xlsx")
                    df_flat.to_excel(file_path_flat, index=False)

                    print("Flattened data saved to", file_path_flat)

    # Save the entire workbook to the Excel file
    workbook.save("Output.xlsx")
    print('Excel file "Output.xlsx" saved.')
