import pandas as pd
from openpyxl import load_workbook
from datetime import datetime

n_days = {
    "January" : 31,
    "February" : 28,
    "March" : 31,
    "April" : 30,
    "May" : 31,
    "June" : 30,
    "July" : 31,
    "August" : 31,
    "September" : 30,
    "October" : 31,
    "November" : 30,
    "December" : 31
}

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

def get_customer_info(service, customer_name):
    df = pd.read_excel(EXCEL_PATH, sheet_name=service)
    customer_row = df[df['Customer Name'].str.strip() == customer_name.strip()]
    
    current_values = {}
    if not customer_row.empty:
        row = customer_row.iloc[0]
        current_values = {
            'usage': row.get('Usage (%)', ''),
            'cost': row.get('Unit Price', ''),
            'period': row.get('Consumption Period', '')
        }
    
    return current_values

def update_customer_info(service, customer_name, updates):
    print(f"Updating {customer_name} in {service} with: {updates}")
    
    # Load the sheet to update
    df = pd.read_excel(EXCEL_PATH, sheet_name=service)
    
    try:
        idx = df[df['Customer Name'].str.strip() == customer_name.strip()].index[0]
        df.at[idx, 'Month'] = datetime.now().strftime('%B')
    except IndexError:
        print(f"Customer '{customer_name}' not found in {service} sheet.")
        return
    
    for field, value in updates.items():
        if value.strip():
            excel_field = FIELD_MAP.get(field, field)  # fallback to original field if not in map
            print(f"Updating '{excel_field}' to '{value}'")
            df.at[idx, excel_field] = value.strip()      
    
    df.at[idx, 'Consumption Duration'] = round(float(df.at[idx, 'Consumption Period']) / n_days[datetime.now().strftime('%B')], 2)
    df.at[idx, 'Net Price'] = float(df.at[idx, 'Consumption Duration']) * float(df.at[idx, 'Usage (%)']) * float(df.at[idx, 'Unit Price']) / 100
    
    # Read all sheets before writing
    all_sheets = pd.read_excel(EXCEL_PATH, sheet_name=None)
    all_sheets[service] = df  # Replace updated sheet

    # Now safely write back all sheets
    with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl', mode='w') as writer:
        for sheet_name, sheet_df in all_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print("Excel update completed.")

