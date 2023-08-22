import os
import pandas as pd

# Path to your Excel file
excel_file_path = 'Indicator_flat.xlsx'

# Path to the directory containing folders to be renamed
folder_base_path = '/home/kidus/Documents/Automation/data/ghoapi.azureedge.net/u'

# Load the Excel file into a DataFrame
excel_data = pd.read_excel(excel_file_path)
print(excel_data)

# Loop through the rows in the DataFrame
for index, row in excel_data.iterrows():
    indicator_code = str(row['INDICATOR_CODE'])  # Convert to string in case it's numeric
    indicator_name = str(row['INDICATOR_NAME'])

    old_folder_path = os.path.join(folder_base_path, indicator_code)
    new_folder_path = os.path.join(folder_base_path, indicator_name)

    # Rename the folder
    try:
        os.rename(old_folder_path, new_folder_path)
        print(f"Renamed '{indicator_code}' to '{indicator_name}'")
    except FileNotFoundError:
        print(f"Folder '{indicator_code}' not found.")

print("Renaming process completed.")
