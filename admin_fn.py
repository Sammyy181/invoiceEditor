import json
import os
from datetime import datetime
import pandas as pd

TEMPLATE_FILE = 'template.xlsx'

FIXED_COLUMNS = [
    {'id': 'fixed_1', 'title': 'Customer Name', 'type': 'text'},
    {'id': 'fixed_2', 'title': 'Unit Price', 'type': 'integer'},
    {'id': 'fixed_3', 'title': 'Consumption Percentage', 'type': 'integer'},
    {'id': 'fixed_4', 'title': 'Usage (%)', 'type': 'integer'},
    {'id': 'fixed_5', 'title': 'Consumption Duration', 'type': 'decimal'},
    {'id': 'fixed_6', 'title': 'Net Price', 'type': 'decimal'},
    {'id': 'fixed_7', 'title': 'Remarks', 'type': 'text'},
    {'id': 'fixed_8', 'title': 'Month', 'type': 'text'}
]

def load_columns_from_excel():
    config_file = 'columns_config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return []

def save_columns_to_config(columns):
    config_file = 'columns_config.json'
    with open(config_file, 'w') as f:
        json.dump(columns, f, indent=2)
        
def update_excel_template(columns):
    try:
        all_sheets = pd.read_excel(TEMPLATE_FILE, sheet_name=None)
        now = datetime.now()
        current_month = now.strftime('%B')
        # Combine fixed columns with dynamic columns
        all_columns = FIXED_COLUMNS + columns
        
        if not all_columns:
            df = pd.DataFrame()
        else:
            column_names = [col['title'] for col in all_columns]
            df = pd.DataFrame(columns=column_names)
            
        all_sheets[current_month] = df
        with pd.ExcelWriter(TEMPLATE_FILE, engine='openpyxl', mode='w') as writer:
            for sheet_name, sheet_df in all_sheets.items():
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
    except Exception as e:
        print(f"Error updating Excel template: {e}")
        
def load_titles():
    config_file = 'titles_config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return []

def save_titles(titles):
    config_file = 'titles_config.json'
    with open(config_file, 'w') as f:
        json.dump(titles, f, indent=4)
        
