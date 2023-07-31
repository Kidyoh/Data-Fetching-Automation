import os
import requests 
import pandas as pd
import urllib.parse

# Function to clean XML data
def clean_xml(xml_data):
    start = xml_data.find('<?xml version')
    if start > -1:
        return xml_data[start:]
    else:
        return None

# Save XML file 
def save_xml(xml_data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(xml_data)
        
def xml_to_excel(xml_data, excel_file):

    # Read data into DataFrame
    df = pd.read_xml(xml_data)

    # Get root tags 
    root_tags = df.columns.get_level_values(0).unique().tolist()

    # Create Excel writer
    writer = pd.ExcelWriter(excel_file, engine='openpyxl')  

    # Loop through root tags
    for tag in root_tags:
      
        # Filter columns by tag
        tag_cols = [col for col in df.columns if col[0] == tag]  
        tag_df = df[tag_cols]
        
        # Expand nested columns
        tag_df = tag_df.apply(lambda x: x.str.split('|').explode())
        
        # Save to sheet
        tag_df.to_excel(writer, sheet_name=tag, index=False)

    # Save Excel file 
    writer.close()
    
        
# Main function    
if __name__ == '__main__':

    # Get API URL
    url = input('Enter API URL: ')  
    parsed = urllib.parse.urlparse(url)

    # Create directories
    root_dir = 'data'
    source_dir = os.path.join(root_dir, parsed.hostname)
    data_dir = os.path.join(source_dir, parsed.path.split('/')[-1])
    os.makedirs(data_dir, exist_ok=True)

    # Make API request
    response = requests.get(url)

    # Check response
    if response.status_code == 200:
        print('API request succeeded') 

        # Clean XML data
        xml_data = response.text
        clean_xml_data = clean_xml(xml_data)

        # Save XML file
        xml_file = os.path.join(data_dir, 'data.xml')
        save_xml(clean_xml_data, xml_file)
        
        # Convert to Excel
        excel_file = os.path.join(data_dir, '{data}.xlsx') 
        xml_to_excel(xml_file, excel_file)

        print('Data saved to Excel')

    else:
        print('API request failed')