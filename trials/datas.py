import requests
import xml.etree.ElementTree as ET
import pandas as pd
import xmltodict

# Make an API request and get the XML response
api_url = 'https://apps.who.int/gho/athena/api/'
response = requests.get(api_url)
xml_data = response.content

# Parse the XML data
root = ET.fromstring(xml_data)

# Parse the XML data into a dictionary
data_dict = xmltodict.parse(xml_data)

# Extract attribute values and create a list of dictionaries
structured_data = []
for dataset in data_dict['Root']['Dataset']:
    dataset_label = dataset['@Label']
    for attribute in dataset['Attribute']:
        attribute_label = attribute['@Label']
        attribute_value = attribute['Display']
        structured_data.append({
            'Dataset': dataset_label,
            'Attribute': attribute_label,
            'Value': attribute_value
        })

# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(structured_data)

# Save the DataFrame to an Excel file
output_file = 'structured_data.xlsx'
df.to_excel(output_file, index=False, engine='openpyxl')

print(f"Structured data saved to {output_file}")
