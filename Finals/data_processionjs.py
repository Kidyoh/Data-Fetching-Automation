import urllib.parse
import os
import requests
import json
import pandas as pd


url = input("Enter API URL: ")

# url = "https://api.worldbank.org/pip/v1/pip?country=SSA&year=2008&povline=1.9&fill_gaps=false"

parsed = urllib.parse.urlparse(url)
params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)

country = params.get('country', 'unknown')[0]
source = parsed.hostname # worldbank.org
datapoint = parsed.path.split('/')[-1] # population

root_dir = 'data'
source_dir = os.path.join(root_dir, source)
country_dir = os.path.join(source_dir, country)
datapoint_dir = os.path.join(country_dir, datapoint) 

os.makedirs(datapoint_dir, exist_ok=True)


# if country == 'ETH':
  
response = requests.get(url)
data = response.json()

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
if isinstance(data, dict):
    flat_data = flatten(data)
else:
    flat_data = flatten({"data": data})

# Create DataFrame from the flattened data
df_flat = pd.DataFrame.from_dict(flat_data)

# Save the flattened data to an Excel file
file_path_flat = os.path.join(datapoint_dir, f"{datapoint}_flat.xlsx")
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
with pd.ExcelWriter(os.path.join(datapoint_dir, f"{datapoint}_of_{country}.xlsx")) as writer:
    for country_code, df in dfs_by_country.items():
        df.to_excel(writer, sheet_name=country_code, index=False)

print("Data saved by country to", os.path.join(datapoint_dir, f"{datapoint}_of_{country}.xlsx"))