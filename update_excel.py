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
TAX_CONFIG_FILE = 'tax_config.json'

def load_column_map(service):
    with open(f'titles/{service}.json') as f:
        titles_config = json.load(f)

    COLUMN_MAP = {
        'customer_name': next(col['title'] for col in titles_config if col['id'] == 'fixed_1'),
        'unit_price':     next(col['title'] for col in titles_config if col['id'] == 'fixed_2'),
        'period':         next(col['title'] for col in titles_config if col['id'] == 'fixed_3'),
        'usage':          next(col['title'] for col in titles_config if col['id'] == 'fixed_4'),
        'consumption':    next(col['title'] for col in titles_config if col['id'] == 'fixed_5'),
        'net_price':      next(col['title'] for col in titles_config if col['id'] == 'fixed_6'),
        'category':        next(col['title'] for col in titles_config if col['id'] == 'fixed_7'),
        'month':          next(col['title'] for col in titles_config if col['id'] == 'fixed_8'),
    }
    
    return COLUMN_MAP

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
        df = pd.read_excel(filepath, sheet_name=previous_month)
        df = df[0:0]
    COLUMN_MAP = load_column_map(service)
    return df[COLUMN_MAP['customer_name']].tolist()

def get_customer_info(service, customer_name):
    path = f'data/{service}.xlsx'
    xls = pd.read_excel(path, sheet_name=None)
    current_values = {}
    
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month_date = now - relativedelta(months=1) 
    previous_month = previous_month_date.strftime('%B')
    COLUMN_MAP = load_column_map(service)
    
    if current_month in xls:
        df = xls[current_month]
        customer_row = df[df['Customer Name'].str.strip() == customer_name.strip()]
        if not customer_row.empty:
            row = customer_row.iloc[0]
            current_values = {
                'usage': row.get(COLUMN_MAP['usage'], ''),
                'cost': row.get(COLUMN_MAP['unit_price'], ''),
                'period': row.get(COLUMN_MAP['period'], '')
            }
            return current_values
    
    if previous_month in xls:
        df_prev = xls[previous_month]
        customer_row_prev = df_prev[df_prev['Customer Name'].str.strip() == customer_name.strip()]
        if not customer_row_prev.empty:
            row = customer_row_prev.iloc[0]
            current_values = {
                'usage': row.get(COLUMN_MAP['usage'], ''),
                'cost': row.get(COLUMN_MAP['unit_price'], ''),
                'period': row.get(COLUMN_MAP['period'], '')
            }
    
    return current_values

def add_customer_info(service, name, price, period, usage, category, others=None):
    path = f'data/{service}.xlsx'
    category_path = f'categories/{service}.xlsx'
    COLUMN_MAP = load_column_map(service)
    
    price = float(price)
    period = float(period)
    usage = float(usage)
    
    if os.path.exists(category_path):
        with open(category_path, 'r') as f:
            categories = json.load(f)
        for cat in categories:
            if cat.get('id') == category:
                category = cat.get('name')
                break 
    
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month = now - relativedelta(months=1)
    previous_month = previous_month.strftime('%B')

    all_sheets = pd.read_excel(path, sheet_name=None)

    if current_month in all_sheets:
        df = all_sheets[current_month].copy()
        print(f"Editing existing sheet for {current_month}.")
    
    else:
        df = all_sheets[previous_month].copy()
        
    idx = len(df)
    
    df.at[idx, COLUMN_MAP['customer_name']] = name
    df.at[idx, COLUMN_MAP['unit_price']] = price
    df.at[idx, COLUMN_MAP['period']] = period
    df.at[idx, COLUMN_MAP['usage']] = usage
    df.at[idx, COLUMN_MAP['consumption']] = round(period / n_days[current_month], 2)
    df.at[idx, COLUMN_MAP['net_price']] = price * usage / 100 * (period / n_days[current_month])
    df.at[idx, COLUMN_MAP['month']] = current_month
    df.at[idx, COLUMN_MAP['category']] = category
    
    if others:
        for key, value in others.items():
            col_name = key
            if col_name not in df.columns:
                print(f"Adding new column '{col_name}' for dynamic field.")
                df[col_name] = '' 
            df.at[idx, col_name] = value
    
    all_sheets[current_month] = df
    
    with pd.ExcelWriter(path, engine='openpyxl', mode='w') as writer:
        for sheet_name, sheet_df in all_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
       
def update_customer_info(service, customer_name, updates):
    print(f"Updating {customer_name} in {service} with: {updates}")
    path = f'data/{service}.xlsx'
    COLUMN_MAP = load_column_map(service)
    
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month = now - relativedelta(months=1)
    previous_month = previous_month.strftime('%B')
    
    try:
        with open(f'columns/{service}.json') as f:
            config = json.load(f)
        FIELD_MAP = {col['title'].lower(): col['title'] for col in config}
        FIELD_MAP.update({
            'usage': COLUMN_MAP['usage'],
            'cost': COLUMN_MAP['unit_price'],
            'period': COLUMN_MAP['period'],
            'category' : COLUMN_MAP['category']
        })
    except Exception as e:
        print(f"Error reading columns_config.json: {e}")
        FIELD_MAP = {
            'usage': COLUMN_MAP['usage'],
            'cost': COLUMN_MAP['unit_price'],
            'period': COLUMN_MAP['period'],
            'category' : COLUMN_MAP['category']
        }

    all_sheets = pd.read_excel(path, sheet_name=None)

    if current_month in all_sheets:
        df = all_sheets[current_month].copy()
        print(f"Editing existing sheet for {current_month}.")
    elif previous_month in all_sheets:
        df = all_sheets[previous_month].copy()
        df = df[0:0]
        df['Month'] = current_month  
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
    
    try:
        with open(f'categories/{service}.json') as f:  
            category_map = json.load(f)  
            id_to_name = {str(item['id']): item['name'] for item in category_map}
    except Exception as e:
        print(f"Error loading category JSON for mapping: {e}")
        id_to_name = {}

    for field, value in updates.items():
        value = value.strip()
        if not value:
            continue

        excel_field = FIELD_MAP.get(field, field)

        if field == 'category':
            original_value = value
            value = id_to_name.get(value, value)  
            print(f"Mapping category ID '{original_value}' to name '{value}'")

        if excel_field not in df.columns:
            print(f"Column '{excel_field}' not found in sheet, creating it.")
            df[excel_field] = ''

        print(f"Updating '{excel_field}' to '{value}'")
        df.at[idx, excel_field] = value

    df.at[idx, COLUMN_MAP['consumption']] = round(
        float(df.at[idx, COLUMN_MAP['period']]) / n_days[current_month], 2
    )
    df.at[idx, 'Net Price'] = round((
        float(df.at[idx, COLUMN_MAP['consumption']]) *
        float(df.at[idx, COLUMN_MAP['usage']]) *
        float(df.at[idx, COLUMN_MAP['unit_price']]) / 100
    ), 2)

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
        df = pd.read_excel(path, sheet_name=previous_month)
    else:  
        df = pd.read_excel(path, sheet_name=current_month)  
    df = df.where(pd.notnull(df), 'N/A')  
    return df

def copy_previous_data(service):
    
    path = f'data/{service}.xlsx'
    COLUMN_MAP = load_column_map(service)
    
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month = now - relativedelta(months=1)
    previous_month = previous_month.strftime('%B')
    
    all_sheets = pd.read_excel(path, sheet_name=None)
    
    if current_month in all_sheets:
        df = all_sheets[current_month].copy()
        copied = all_sheets[previous_month].copy()
        copied[COLUMN_MAP['month']] = current_month

        copied[COLUMN_MAP['period']] = pd.to_numeric(copied[COLUMN_MAP['period']], errors='coerce')
        copied[COLUMN_MAP['usage']] = pd.to_numeric(copied[COLUMN_MAP['usage']], errors='coerce')
        copied[COLUMN_MAP['unit_price']] = pd.to_numeric(copied[COLUMN_MAP['unit_price']], errors='coerce')

        copied[COLUMN_MAP['consumption']] = (
            copied[COLUMN_MAP['period']] / n_days[current_month]
        ).round(2)

        copied[COLUMN_MAP['net_price']] = (
            copied[COLUMN_MAP['consumption']] *
            copied[COLUMN_MAP['usage']] *
            copied[COLUMN_MAP['unit_price']] / 100
        ).round(2)

        df = pd.concat([df, copied], ignore_index=True)

    elif previous_month in all_sheets:
        df = all_sheets[previous_month].copy()
        df[COLUMN_MAP['month']] = current_month

        df[COLUMN_MAP['period']] = pd.to_numeric(df[COLUMN_MAP['period']], errors='coerce')
        df[COLUMN_MAP['usage']] = pd.to_numeric(df[COLUMN_MAP['usage']], errors='coerce')
        df[COLUMN_MAP['unit_price']] = pd.to_numeric(df[COLUMN_MAP['unit_price']], errors='coerce')

        df[COLUMN_MAP['consumption']] = (
            df[COLUMN_MAP['period']] / n_days[current_month]
        ).round(2)

        df[COLUMN_MAP['net_price']] = (
            df[COLUMN_MAP['consumption']] *
            df[COLUMN_MAP['usage']] *
            df[COLUMN_MAP['unit_price']] / 100
        ).round(2)
    
    all_sheets[current_month] = df
    
    with pd.ExcelWriter(path, engine='openpyxl', mode='w') as writer:
        for sheet_name, sheet_df in all_sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
def get_dropdown(service):
    file_path = f'categories/{service}.json'
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []
    
def download_data(service, type):
    now = datetime.now()
    current_month = now.strftime('%B')
    previous_month = now - relativedelta(months=1)
    previous_month = previous_month.strftime('%B')
    file_path = f'data/{service}.xlsx'
    COLUMN_MAP = load_column_map(service)
    tax_data = load_tax_config
    default_cgst = 0.09
    default_sgst = 0.09

    # Get tax rates with defaults
    service_tax = tax_data.get(service, {})
    cgst_per = service_tax.get("cgst", default_cgst)
    sgst_per = service_tax.get("sgst", default_sgst)
    
    try:
        if type == 'view':
            df = pd.read_excel(file_path, sheet_name=previous_month)
        else:
            df = pd.read_excel(file_path, sheet_name=current_month)
        
        blank_row = pd.Series([None] * df.shape[1], index=df.columns)
        df = pd.concat([df, pd.DataFrame([blank_row])], ignore_index=True)
        
        value_col = df.columns[-1]
        title_col = df.columns[-2]
        
        df[COLUMN_MAP['net_price']] = pd.to_numeric(df[COLUMN_MAP['net_price']], errors='coerce')
        
        net_total = df[COLUMN_MAP['net_price']].dropna().sum()
        cgst = round(net_total * cgst_per, 2)
        sgst = round(net_total * sgst_per, 2)
        grand_total = round(net_total + cgst + sgst, 2)
        
        totals = [
            {title_col: "Net Total (Before Tax)", value_col: net_total},
            {title_col: "CGST", value_col: cgst},
            {title_col: "SGST", value_col: sgst},
            {title_col: "Grand Total", value_col: grand_total}
        ]
        
        df = pd.concat([df, pd.DataFrame(totals)], ignore_index=True)
        output_path = f'{service}_{type}.xlsx'
        df.to_excel(output_path, index=False)
        print(f"Saved processed sheet as '{output_path}'")
        return output_path
            
    except Exception as e:
        return e

def load_tax_config():
    if not os.path.exists(TAX_CONFIG_FILE):
        return {}
    with open(TAX_CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_service_tax(service):
    data = load_tax_config()
    return data.get(service, {'cgst': 0.09, 'sgst': 0.09})

def update_service_tax(service, cgst, sgst):
    data = load_tax_config()
    data[service] = {'cgst': cgst, 'sgst': sgst}
    with open(TAX_CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)
