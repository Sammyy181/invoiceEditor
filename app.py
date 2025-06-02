from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from update_excel import get_services, get_customers, update_customer_info, get_customer_info, add_customer_info, your_invoice_function, copy_previous_data
from admin_fn import *
import os
import shutil
from datetime import datetime
from openpyxl import load_workbook
from dateutil.relativedelta import relativedelta

# Get current month as full name (e.g., "May")
month_name = datetime.now().strftime("%B")

app = Flask(__name__)
app.secret_key = 'your-secret-key'

TEMPLATE_FILE = 'template.xlsx'
SERVICE_FOLDER = 'data'  
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

now = datetime.now()
previous_month_date = now - relativedelta(months=1)
previous_month_name = previous_month_date.strftime('%B')

wb = load_workbook(TEMPLATE_FILE)
first_sheet = wb.worksheets[0]  # or wb.active
second_sheet = wb.worksheets[1]
first_sheet.title = previous_month_name
second_sheet.title = month_name
wb.save(TEMPLATE_FILE)

@app.route('/')
def home():
    return redirect(url_for('select_service'))

@app.route('/select_service', methods=['GET', 'POST'])
def select_service():
    services = get_services()
    if request.method == 'POST':
        session['service'] = request.form['service']
        return redirect(url_for('select_customer'))
    return render_template('select_service.html', services=services)

@app.route('/add_service', methods=['POST'])
def add_service():
    service_name = request.form.get('service_name', '').strip()
    
    if not service_name:
        return "No service name provided", 400

    # Sanitize and construct the path
    filename = f"{service_name}.xlsx"
    dest_path = os.path.join(SERVICE_FOLDER, filename)

    # Check if file already exists
    if os.path.exists(dest_path):
        return "Service already exists", 409

    try:
        shutil.copyfile(TEMPLATE_FILE, dest_path)
        print(f"Created new service file: {dest_path}")
        return redirect(url_for('select_service'))
    except Exception as e:
        return f"Failed to create new service: {str(e)}", 500

@app.route('/select_feature', methods=['GET', 'POST'])
def select_feature():
    service = session.get('service')
    if not service:
        return redirect(url_for('select_service'))
    
    if request.method == 'POST':
        feature = request.form['feature']
        
        if feature == 'update_preferences':
            return redirect(url_for('select_customer'))
        elif feature == 'view_invoice':
            # Add your invoice viewing logic here
            return render_template('coming_soon.html', feature='View Last Generated Invoice')
        elif feature == 'generate_invoice':
            # Add your invoice generation logic here
            return render_template('coming_soon.html', feature='Generate New Invoice')
        elif feature == 'manage_customer':
            # Add your customer management logic here
            return render_template('coming_soon.html', feature='Add or Delete Customer')
    
    return render_template('select_feature.html', service=service)

@app.route('/select_customer', methods=['GET', 'POST'])
def select_customer():
    service = session.get('service')
    action = request.form.get('action')
    selected_customer = request.form.get('customer')
    customers = get_customers(service)

    if request.method == 'POST':
        if action == 'add_new':
            # This just re-renders the page with the popup showing
            try:
                with open('columns_config.json') as f:
                    columns_config = json.load(f)
            except Exception:
                columns_config = []
                
            dynamic_fields = []
            for col in columns_config:
                # Normalize title to a safe form name (lowercase, underscores instead of spaces)
                field_name = col['title'].lower().replace(' ', '_')
                dynamic_fields.append({
                    'name': field_name,
                    'label': col['title'],
                    'type': col.get('type', 'text')  # fallback to text input
                })
            
            return render_template('select_customer.html', customers=customers, service=service, show_popup=True, dynamic_fields=dynamic_fields)
        elif action == 'copy_previous':
            copy_previous_data(service=service)
            return redirect(url_for('select_customer'))
        elif selected_customer:
            session['customer'] = selected_customer
            current = get_customer_info(service, selected_customer)
            
            try:
                with open('columns_config.json') as f:
                    columns_config = json.load(f)
            except Exception:
                columns_config = []
                
            dynamic_fields = []
            for col in columns_config:
                # Normalize title to a safe form name (lowercase, underscores instead of spaces)
                field_name = col['title'].lower().replace(' ', '_')
                dynamic_fields.append({
                    'name': field_name,
                    'label': col['title'],
                    'type': col.get('type', 'text')  # fallback to text input
                })

            
            return render_template(
                'select_customer.html',
                customers=customers,
                service=service,
                show_edit_popup=True,
                current=current,
                dynamic_fields=dynamic_fields
            )

    return render_template('select_customer.html', customers=customers, service=service, show_popup=False)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    service = session.get('service')
    
    name = request.form['customer_name']
    price = float(request.form['unit_price'])
    period = int(request.form['consumption_period'])
    usage = float(request.form['usage_percent'])
    
    other_data = {}
    
    try:
        with open('columns_config.json') as f:
            columns = json.load(f)
    except Exception as e:
        flash(f"Failed to load field configuration: {str(e)}", "error")
        return redirect(url_for('select_customer'))
    
    for col in columns:
        field_name = col['title']
        if field_name in request.form:
            val = request.form[field_name].strip()
            if val != '':
                other_data[field_name] = val

    add_customer_info(service, name, price, period, usage, other_data)
    
    flash("Added Customer Information Successfully!")
    return redirect(url_for('select_customer'))


@app.route('/update_customer', methods=['POST'])
def update_customer():
    # Make sure these session keys exist
    service = session.get('service')
    customer = session.get('customer')

    if not service or not customer:
        flash("Session expired or invalid. Please select a customer again.", "error")
        return redirect(url_for('select_customer'))
    
    try:
        with open('columns_config.json') as f:
            columns_config = json.load(f)
    except Exception as e:
        flash(f"Failed to load field configuration: {str(e)}", "error")
        return redirect(url_for('select_customer'))
    
    allowed_fields = {col['title'].lower() for col in columns_config}
    allowed_fields.update({'usage', 'cost', 'period'})

    # Filter out empty values, so only updated fields are sent
    updates = {
        k: v.strip() for k, v in request.form.items()
        if k in allowed_fields and v.strip() != ''
    }
    
    if not updates:
        flash("No valid fields provided for update.", "warning")
        return redirect(url_for('select_customer'))

    try:
        update_customer_info(service, customer, updates)
        flash("Customer Updated Successfully!", "success")
    except Exception as e:
        flash(f"Failed to update customer: {str(e)}", "error")

    return redirect(url_for('select_customer'))

@app.route('/get_invoice_data', methods=['POST'])
def get_invoice_data():
    try:
        data = request.get_json()
        action = data.get('action')  
        service = data.get('service')
        
        df = your_invoice_function(action, service) 
        df.drop(['Remarks', 'Month'], axis=1, inplace=True, errors='ignore')
        
        total = df['Net Price'].sum()
        
        response_data = {
            'columns': df.columns.tolist(),
            'data': df.values.tolist(),
            'summary': None 
        }
        
        if len(df):
            response_data['summary'] = {
                'Grand Total' : total
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/columns', methods=['GET'])
def get_columns():
    """Get all configured columns"""
    try:
        columns = load_columns_from_excel()
        return jsonify(columns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/columns', methods=['POST'])
def add_column():
    """Add a new column configuration"""
    try:
        print("Received POST request to /api/columns")
        
        data = request.get_json()
        print(f"Request data: {data}")
        
        if not data or 'title' not in data or 'type' not in data:
            print("Missing title or type in request")
            return jsonify({'error': 'Title and type are required'}), 400
        
        print("Loading existing columns...")
        columns = load_columns_from_excel()
        print(f"Existing columns: {columns}")
        
        # Check if column already exists in both fixed and dynamic columns
        all_existing_titles = [col['title'].lower() for col in FIXED_COLUMNS] + [col['title'].lower() for col in columns]
        print(f"All existing titles: {all_existing_titles}")
        
        if data['title'].lower() in all_existing_titles:
            print(f"Column title '{data['title']}' already exists")
            return jsonify({'error': 'Column title already exists'}), 400
        
        # Create new column with unique ID
        new_column = {
            'id': str(len(FIXED_COLUMNS) + len(columns) + 1),
            'title': data['title'],
            'type': data['type'],
            'created_at': datetime.now().isoformat()
        }
        print(f"Creating new column: {new_column}")
        
        columns.append(new_column)
        print("Saving columns to config...")
        save_columns_to_config(columns)
        
        print("Updating Excel template...")
        update_excel_template(columns)
        
        print("Column added successfully")
        return jsonify(new_column), 201
        
    except Exception as e:
        print(f"Error in add_column: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/columns/<column_id>', methods=['DELETE'])
def remove_column(column_id):
    """Remove a column configuration"""
    try:
        columns = load_columns_from_excel()
        
        # Find and remove column
        original_length = len(columns)
        columns = [col for col in columns if col['id'] != column_id]
        
        if len(columns) == original_length:
            return jsonify({'error': 'Column not found'}), 404
        
        save_columns_to_config(columns)
        update_excel_template(columns)
        
        return jsonify({'message': 'Column removed successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
