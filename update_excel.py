import pandas as pd
from openpyxl import load_workbook
from datetime import datetime
import os
from dateutil.relativedelta import relativedelta
import json

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
    service_files = os.listdir('data')
    services = [f[:-5] for f in service_files if f.endswith('.xlsx')]
    return services

def get_customers(service):
    filepath = f'data/{service}.xlsx'
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month = now - relativedelta(months=1) 
    previous_month = previous_month.strftime('%B')
    
    try:
        df = pd.read_excel(filepath, sheet_name=current_month)
    except Exception:
        # If current month not found, fall back to previous
        df = pd.read_excel(filepath, sheet_name=previous_month)
        df = df[0:0]
    return df['Customer Name'].tolist()

FIELD_MAP = {
    'usage': 'Usage (%)',
    'cost': 'Unit Price',
    'period' : 'Consumption Period',
    
    # Add more if needed
}

def get_customer_info(service, customer_name):
    path = f'data/{service}.xlsx'
    xls = pd.read_excel(path, sheet_name=None)
    current_values = {}
    
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month_date = now - relativedelta(months=1) 
    previous_month = previous_month_date.strftime('%B')
    
    if current_month in xls:
        df = xls[current_month]
        customer_row = df[df['Customer Name'].str.strip() == customer_name.strip()]
        if not customer_row.empty:
            row = customer_row.iloc[0]
            current_values = {
                'usage': row.get('Usage (%)', ''),
                'cost': row.get('Unit Price', ''),
                'period': row.get('Consumption Period', '')
            }
            return current_values
    
    if previous_month in xls:
        df_prev = xls[previous_month]
        customer_row_prev = df_prev[df_prev['Customer Name'].str.strip() == customer_name.strip()]
        if not customer_row_prev.empty:
            row = customer_row_prev.iloc[0]
            current_values = {
                'usage': row.get('Usage (%)', ''),
                'cost': row.get('Unit Price', ''),
                'period': row.get('Consumption Period', '')
            }
    
    return current_values

def add_customer_info(service, name, price, period, usage):
    path = f'data/{service}.xlsx'
    
    price = float(price)
    period = float(period)
    usage = float(usage)
    
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month = now - relativedelta(months=1)
    previous_month = previous_month.strftime('%B')

    # Read all sheets from the file
    all_sheets = pd.read_excel(path, sheet_name=None)

    if current_month in all_sheets:
        # Current month sheet exists, edit it directly
        df = all_sheets[current_month].copy()
        print(f"Editing existing sheet for {current_month}.")
    
    else:
        df = all_sheets[previous_month].copy()
        
    idx = len(df)
    
    df.at[idx, 'Customer Name'] = name
    df.at[idx, 'Unit Price'] = price
    df.at[idx, 'Consumption Period'] = period
    df.at[idx, 'Usage (%)'] = usage
    df.at[idx, 'Consumption Duration'] = round(period/n_days[current_month], 2)
    df.at[idx, 'Net Price'] = float(df.at[idx, 'Consumption Duration']) * price * usage/100
    df.at[idx, 'Month'] = current_month
    
    all_sheets[current_month] = df
    
    with pd.ExcelWriter(path, engine='openpyxl', mode='w') as writer:
        for sheet_name, sheet_df in all_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
       
def update_customer_info(service, customer_name, updates):
    print(f"Updating {customer_name} in {service} with: {updates}")
    path = f'data/{service}.xlsx'
    
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month = now - relativedelta(months=1)
    previous_month = previous_month.strftime('%B')

    # Read all sheets from the file
    all_sheets = pd.read_excel(path, sheet_name=None)

    if current_month in all_sheets:
        # Current month sheet exists, edit it directly
        df = all_sheets[current_month].copy()
        print(f"Editing existing sheet for {current_month}.")
    elif previous_month in all_sheets:
        # Current month sheet missing, copy previous month sheet as base
        df = all_sheets[previous_month].copy()
        df = df[0:0]
        df['Month'] = current_month  # Update Month column for all rows just in case
        print(f"Creating new sheet for {current_month} from {previous_month}.")
    else:
        print(f"Neither current month ({current_month}) nor previous month ({previous_month}) sheets found in {service} file.")
        return

    try:
        idx = df[df['Customer Name'].str.strip() == customer_name.strip()].index[0]
    except IndexError:
        print(f"Customer '{customer_name}' not found in {service} sheet '{current_month}'.")
        return

    df.at[idx, 'Month'] = current_month

    # Apply updates only if values are non-empty after stripping
    for field, value in updates.items():
        if value.strip():
            excel_field = FIELD_MAP.get(field, field)  # Use FIELD_MAP or fallback
            print(f"Updating '{excel_field}' to '{value.strip()}'")
            df.at[idx, excel_field] = value.strip()

    df.at[idx, 'Consumption Duration'] = round(
        float(df.at[idx, 'Consumption Period']) / n_days[current_month], 2
    )
    df.at[idx, 'Net Price'] = (
        float(df.at[idx, 'Consumption Duration']) *
        float(df.at[idx, 'Usage (%)']) *
        float(df.at[idx, 'Unit Price']) / 100
    )

    all_sheets[current_month] = df

    with pd.ExcelWriter(path, engine='openpyxl', mode='w') as writer:
        for sheet_name, sheet_df in all_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Excel update for {current_month} completed successfully.")

def your_invoice_function(action, service):
    
    path = f'data/{service}.xlsx'
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month = now - relativedelta(months=1)
    previous_month = previous_month.strftime('%B')
    
    if action == 'view':
        print(previous_month)
        df = pd.read_excel(path, sheet_name=previous_month)
    else:  
        df = pd.read_excel(path, sheet_name=current_month)    
    return df

def copy_previous_data(service):
    
    path = f'data/{service}.xlsx'
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month = now - relativedelta(months=1)
    previous_month = previous_month.strftime('%B')
    
    all_sheets = pd.read_excel(path, sheet_name=None)
    
    if current_month in all_sheets:
        df = all_sheets[current_month].copy()
        copied = all_sheets[previous_month].copy()
        copied['Month'] = current_month
        copied['Consumption Period'] = pd.to_numeric(copied['Consumption Period'], errors='coerce')
        copied['Usage (%)'] = pd.to_numeric(copied['Usage (%)'], errors='coerce')
        copied['Unit Price'] = pd.to_numeric(copied['Unit Price'], errors='coerce')
        copied['Consumption Duration'] = (copied['Consumption Period'] / n_days[current_month]).round(2)
        copied['Net Price'] = (copied['Consumption Duration'] * copied['Usage (%)'] * copied['Unit Price']/ 100).round(2)
        
        
        df = pd.concat([df, copied], ignore_index=True)
    elif previous_month in all_sheets:
        df = all_sheets[previous_month].copy()
        df['Month'] = current_month
        df['Consumption Period'] = pd.to_numeric(df['Consumption Period'], errors='coerce')
        df['Usage (%)'] = pd.to_numeric(df['Usage (%)'], errors='coerce')
        df['Unit Price'] = pd.to_numeric(df['Unit Price'], errors='coerce')
        df['Consumption Duration'] = (df['Consumption Period'] / n_days[current_month]).round(2)
        df['Net Price'] = (df['Consumption Duration'] * df['Usage (%)'] * df['Unit Price']/ 100).round(2)
    
    all_sheets[current_month] = df
    
    with pd.ExcelWriter(path, engine='openpyxl', mode='w') as writer:
        for sheet_name, sheet_df in all_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        