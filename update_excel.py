import pandas as pd
from openpyxl import load_workbook

def get_services():
    wb = pd.ExcelFile('data/services.xlsx')
    return wb.sheet_names

def get_customers(service):
    df = pd.read_excel('data/services.xlsx', sheet_name=service)
    return df['Customer Name'].tolist()

EXCEL_PATH = 'data/services.xlsx'

FIELD_MAP = {
    'usage': 'Usage (%)',
    'cost': 'Unit Price',
    'period' : 'Consumption Period',
    
    # Add more if needed
}

def update_customer_info(service, customer_name, updates):
    print(f"Updating {customer_name} in {service} with: {updates}")
    
    # Load the sheet to update
    df = pd.read_excel(EXCEL_PATH, sheet_name=service)
    
    try:
        idx = df[df['Customer Name'].str.strip() == customer_name.strip()].index[0]
    except IndexError:
        print(f"Customer '{customer_name}' not found in {service} sheet.")
        return
    
    for field, value in updates.items():
        if value.strip():
            excel_field = FIELD_MAP.get(field, field)  # fallback to original field if not in map
            print(f"Updating '{excel_field}' to '{value}'")
            df.at[idx, excel_field] = value.strip()
    
    # Read all sheets before writing
    all_sheets = pd.read_excel(EXCEL_PATH, sheet_name=None)
    all_sheets[service] = df  # Replace updated sheet

    # Now safely write back all sheets
    with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl', mode='w') as writer:
        for sheet_name, sheet_df in all_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print("Excel update completed.")

