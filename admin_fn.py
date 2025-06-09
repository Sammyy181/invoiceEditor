import json
import os
from datetime import datetime
import pandas as pd

TEMPLATE_FILE = 'template.xlsx'

def load_service_columns(service):
    config_file = f'columns/{service}.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return []

def load_service_titles(service):
    title_file = f'titles/{service}.json'
    
    if os.path.exists(title_file):
        with open(title_file, 'r') as f:
            return json.load(f)
    return []

def save_service_columns(service, columns):
    config_file = f'columns/{service}.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'w') as f:
            json.dump(columns, f, indent = 2)
            
def save_service_titles(service, titles):
    title_file = f'titles/{service}.json'
    sheet_path = f'data/{service}.xlsx'
    
    excel_file = pd.ExcelFile(sheet_path)
    sheet_names = excel_file.sheet_names
    
    updated_sheets = {}
    
    for sheet in sheet_names:
        df = pd.read_excel(sheet_path, sheet_name=sheet)
        
        cols = df.columns().tolist()
        for i in range(min(8, len(cols))):
            cols[i] = titles[i]['title']
        df.columns = cols
        
        updated_sheets[sheet] = df
    
    with pd.ExcelWriter(sheet_path, engine='openpyxl') as writer:
        for sheet, df in updated_sheets.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    
    if os.path.exists(title_file):
        with open(title_file, 'w') as f:
            return json.dump(titles, f, indent=4)
    return []
        
