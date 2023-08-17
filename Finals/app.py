from flask import Flask, request, jsonify
import os
import requests
import pandas as pd
import urllib.parse
import xmltodict

app = Flask(__name__)
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

def create_directory(path):
    os.makedirs(path, exist_ok=True)

def fetch_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        content_type = response.headers.get("content-type", "")
        print(content_type)
        return response.content, content_type
    else:
        return None, None

def sanitize_sheet_name(sheet_name):
    invalid_chars = ['\\', '/', '?', '*', '[', ']']
    sanitized_name = ''.join(c for c in sheet_name if c not in invalid_chars)
    return sanitized_name[:31] 

def save_data_to_excel(data, sheet_name, excel_writer):
    sanitized_sheet_name = sanitize_sheet_name(sheet_name)
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                new_sheet_name = f'{sanitized_sheet_name}_{key}'
                if isinstance(value, dict):
                    df = pd.DataFrame(value)
                    df.to_excel(excel_writer, sheet_name=new_sheet_name, index=False)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        new_sheet_name = f'{sanitized_sheet_name}_{i}'
                        df = pd.DataFrame(item)
                        df.to_excel(excel_writer, sheet_name=new_sheet_name, index=False)
            else:
                if isinstance(value, str):
                    data[key] = [value]
                df = pd.DataFrame(data)
                df.to_excel(excel_writer, sheet_name=sheet_name, index=False)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_sheet_name = f'{sheet_name}_{i}'
            if isinstance(item, (dict, list)):
                save_data_to_excel(item, new_sheet_name, excel_writer)

@app.route('/api/', methods=['GET'])
def api_page():
    url = request.args.get('url')

    parsed = urllib.parse.urlparse(url)
    source = parsed.hostname
    datapoint = parsed.path.split('/')[-1]
    root_dir = 'data'
    source_dir = os.path.join(root_dir, source)
    datapoint_dir = os.path.join(source_dir, datapoint)
    
    create_directory(datapoint_dir)

    data, content_type = fetch_data(url)

    if data is not None:
        excel_file = os.path.join(datapoint_dir, f'{datapoint}.xlsx')
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as excel_writer:
            if content_type == 'application/json':
                json_data = data.json()
                save_data_to_excel(json_data, 'root', excel_writer)

            elif content_type == 'text/xml':
                xml_data = data.decode('utf-8')
                xml_data_cleaned = remove_invalid_characters(xml_data)

                if xml_data_cleaned:
                    json_data = xml_to_json(xml_data_cleaned)
                    save_data_to_excel(json_data, 'root', excel_writer)

                    return jsonify({'message': 'Data fetched and processed successfully.'}), 200

                else:
                    return jsonify({'error': 'Unsupported content type. Only XML responses are supported.'}), 400

            else:
                return jsonify({'error': 'Unsupported content type. Only JSON and XML responses are supported.'}), 400

        return jsonify({'message': f'Data fetched and processed successfully. Excel file saved at {excel_file}'}), 200

    else:
        return jsonify({'error': 'Failed to fetch data from the API.'}), 500

if __name__ == '__main__':
    app.run(port=7777)
