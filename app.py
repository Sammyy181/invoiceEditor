from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from update_excel import *
from admin_fn import *
import os
import shutil
from datetime import datetime
from openpyxl import load_workbook
from dateutil.relativedelta import relativedelta
import threading 
import sys

month_name = datetime.now().strftime("%B")

app = Flask(__name__)
app.secret_key = 'your-secret-key'

TEMPLATE_FILE = 'template.xlsx'
SERVICE_FOLDER = 'data'  
TITLES_TEMPLATE = 'titles_config.json'
TITLES_FOLDER = 'titles'
CAT_FOLDER = 'categories'
TAX_CONFIG_FILE = 'tax_config.json' 

now = datetime.now()
previous_month_date = now - relativedelta(months=1)
previous_month_name = previous_month_date.strftime('%B')    

wb = load_workbook(TEMPLATE_FILE)
first_sheet = wb.worksheets[0] 
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

    filename = f"{service_name}.xlsx"
    title_name = f"{service_name}.json"
    dest_path = os.path.join(SERVICE_FOLDER, filename)
    title_path = os.path.join(TITLES_FOLDER, title_name)
    category_path = os.path.join(CAT_FOLDER, title_name)

    if os.path.exists(dest_path):
        return "Service already exists", 409

    try:
        shutil.copyfile(TEMPLATE_FILE, dest_path)
        shutil.copyfile(TITLES_TEMPLATE, title_path)
        with open(category_path, 'w') as f:
            json.dump([], f, indent=4)
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
            return render_template('coming_soon.html', feature='View Last Generated Invoice')
        elif feature == 'generate_invoice':
            return render_template('coming_soon.html', feature='Generate New Invoice')
        elif feature == 'manage_customer':
            return render_template('coming_soon.html', feature='Add or Delete Customer')
    
    return render_template('select_feature.html', service=service)

@app.route('/select_customer', methods=['GET', 'POST'])
def select_customer():
    service = session.get('service')
    action = request.form.get('action')
    selected_customer = request.form.get('customer')
    customers = get_customers(service)
    if service:
        tax_config = get_service_tax(service)
    else:
        tax_config = {'cgst': 0.0, 'sgst': 0.0}

    if request.method == 'POST':
        if action == 'add_new':
            try:
                columns_config = load_service_columns(service)
            except Exception:
                columns_config = []
                
            dynamic_fields = []
            for col in columns_config:
                field_name = col['title'].lower().replace(' ', '_')
                dynamic_fields.append({
                    'name': field_name,
                    'label': col['title'],
                    'type': col.get('type', 'text') 
                })
                
            all_titles = load_service_titles(service)
            wanted_ids = {"fixed_1", "fixed_2", "fixed_3", "fixed_4", "fixed_7"}
            titles = [item for item in all_titles if item["id"] in wanted_ids]
            
            return render_template('select_customer.html', 
                                   customers=customers, 
                                   service=service, 
                                   show_popup=True, 
                                   dynamic_fields=dynamic_fields, 
                                   titles=titles,
                                   tax_config=tax_config)
            
        elif action == 'copy_previous':
            copy_previous_data(service=service)
            return redirect(url_for('select_customer'))
        elif selected_customer:
            session['customer'] = selected_customer
            current = get_customer_info(service, selected_customer)
            
            try:
                columns_config = load_service_columns(service)
            except Exception:
                columns_config = []
                
            dynamic_fields = []
            for col in columns_config:
                field_name = col['title'].lower().replace(' ', '_')
                dynamic_fields.append({
                    'name': field_name,
                    'label': col['title'],
                    'type': col.get('type', 'text') 
                })
            
            all_titles = load_service_titles(service)
            wanted_ids = {"fixed_1", "fixed_2", "fixed_3", "fixed_4", "fixed_7"}
            titles = [item for item in all_titles if item["id"] in wanted_ids]
            
            return render_template(
                'select_customer.html',
                customers=customers,
                service=service,
                show_edit_popup=True,
                current=current,
                dynamic_fields=dynamic_fields,
                titles=titles,
                tax_config=tax_config
            )

    return render_template('select_customer.html', customers=customers, service=service, show_popup=False, tax_config=tax_config)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    service = session.get('service')
    
    name = request.form['customer_name']
    price = float(request.form['unit_price'])
    period = int(request.form['consumption_period'])
    usage = float(request.form['usage_percent'])
    category = request.form['selected_id']
    
    other_data = {}
    
    try:
        columns =load_service_columns(service)
    except Exception as e:
        flash(f"Failed to load field configuration: {str(e)}", "error")
        return redirect(url_for('select_customer'))
    
    for col in columns:
        field_name = col['title']
        if field_name in request.form:
            val = request.form[field_name].strip()
            if val != '':
                other_data[field_name] = val

    add_customer_info(service, name, price, period, usage, category, other_data)
    
    flash("Added Customer Information Successfully!")
    return redirect(url_for('select_customer'))

@app.route('/get_dropdown_options')
def get_dropdown_options():
    service = session.get('service')
    
    options = get_dropdown(service)
    return jsonify(options)


@app.route('/update_customer', methods=['POST'])
def update_customer():
    service = session.get('service')
    customer = session.get('customer')

    if not service or not customer:
        flash("Session expired or invalid. Please select a customer again.", "error")
        return redirect(url_for('select_customer'))
    
    try:
        columns_config = load_service_columns(service)
    except Exception as e:
        flash(f"Failed to load field configuration: {str(e)}", "error")
        return redirect(url_for('select_customer'))
    
    allowed_fields = {col['title'].lower() for col in columns_config}
    allowed_fields.update({'usage', 'cost', 'period', 'category'})

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
        df.drop(['Month'], axis=1, inplace=True, errors='ignore')
        
        net_total = df['Net Price'].sum()
        
        tax_config = get_service_tax(service)
        SGST_RATE = tax_config['sgst']
        CGST_RATE = tax_config['cgst']
        
        sgst_amount = net_total * SGST_RATE
        cgst_amount = net_total * CGST_RATE
        grand_total = net_total + sgst_amount + cgst_amount

        response_data = {
            'columns': df.columns.tolist(),
            'data': df.where(pd.notnull(df), None).values.tolist(),
            'summary': {
                'Net Total': round(net_total, 2),
                'SGST': round(sgst_amount, 2),
                'CGST': round(cgst_amount, 2),
                'Grand Total': round(grand_total, 2)
            },
            'tax_config': {
                'cgst': CGST_RATE,
                'sgst': SGST_RATE
            },
            'service': service
        }

        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_invoice_excel', methods=['POST'])
def download_invoice_excel():
    try:
        data = request.get_json()
        service = data.get('service')
        type = data.get('type')
        file_path = download_data(service, type)    
        
        return send_file(
            file_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{service}_{type}.xlsx'
        )  
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
            
@app.route('/admin')
def admin():
    services = get_services()
    return render_template('admin.html', services=services)

@app.route('/api/columns', methods=['GET'])
def get_columns():
    try:
        service = request.args.get('service')
        if not service:
            return jsonify({'error': 'Service parameter required'}), 400
        
        columns = load_service_columns(service)
        return jsonify(columns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/columns', methods=['POST'])
def add_column():
    try:
        data = request.get_json()
        service = data.get('service')
        
        if not service:
            return jsonify({'error': 'Service parameter required'}), 400
        
        if not data or 'title' not in data or 'type' not in data:
            return jsonify({'error': 'Title and type are required'}), 400
        
        columns = load_service_columns(service)
        fixed_columns = load_service_titles(service)
        
        all_existing_titles = [col['title'].lower() for col in fixed_columns] + [col['title'].lower() for col in columns]
        
        if data['title'].lower() in all_existing_titles:
            return jsonify({'error': 'Column title already exists'}), 400
        
        new_column = {
            'id': str(len(fixed_columns) + len(columns) + 1),
            'title': data['title'],
            'type': data['type'],
            'created_at': datetime.now().isoformat()
        }
        
        columns.append(new_column)
        save_service_columns(service, columns)
        
        return jsonify(new_column), 201
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/columns/<column_id>', methods=['DELETE'])
def remove_column(column_id):
    try:
        service = request.args.get('service')
        if not service:
            return jsonify({'error': 'Service parameter required'}), 400
        
        columns = load_service_columns(service)
        
        original_length = len(columns)
        columns = [col for col in columns if col['id'] != column_id]
        
        if len(columns) == original_length:
            return jsonify({'error': 'Column not found'}), 404
        
        save_service_columns(service, columns)
        
        return jsonify({'message': 'Column removed successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/fixed-columns', methods=['GET'])
def get_fixed_columns():
    service = request.args.get('service')
    if not service:
        return jsonify({'error': 'Service parameter required'}), 400
    
    return jsonify(load_service_titles(service))

@app.route('/api/fixed-columns', methods=['PUT'])
def update_fixed_columns():
    try:
        data = request.get_json()
        service = data.get('service')
        
        if not service:
            return jsonify({'error': 'Service parameter required'}), 400
        
        fixed_columns = data.get('fixedColumns', [])
        save_service_titles(service, fixed_columns)
        
        return jsonify({'message': 'Fixed columns updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/categories', methods = ['GET'])
def get_categories():
    service = request.args.get('service')
    if not service:
        return jsonify({'error': 'Service parameter required'}), 400
    
    return jsonify(load_categories(service))

@app.route('/api/categories', methods=['POST'])
def save_category():
    data = request.json
    service = data.get('service')
    name = data.get('name')
    price = data.get('unitPrice')
    
    if not (service and name and isinstance(price, (int, float))):
        return jsonify({'error': 'Invalid data'}), 400
    
    new_category = add_category(service, name, price)
    return jsonify(new_category), 200

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def edit_category(category_id):
    data = request.json
    service = data.get('service')
    name = data.get('name')
    price = data.get('unitPrice')

    if not (service and name and isinstance(price, (int, float))):
        return jsonify({'error': 'Invalid data'}), 400

    path = f'categories/{service}.json'
    if not os.path.exists(path):
        return jsonify({'error': 'Service not found'}), 404

    with open(path, 'r') as f:
        categories = json.load(f)

    for category in categories:
        if category['id'] == category_id:
            category['name'] = name
            category['unitPrice'] = price
            break
    else:
        return jsonify({'error': 'Category not found'}), 404

    with open(path, 'w') as f:
        json.dump(categories, f, indent=2)

    return jsonify({'message': 'Category updated', 'category': category})

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    service = request.args.get('service')
    if not service:
        return jsonify({'error': 'Service is required'}), 400

    path = f'categories/{service}.json'
    if not os.path.exists(path):
        return jsonify({'error': 'Service not found'}), 404

    with open(path, 'r') as f:
        categories = json.load(f)

    filtered = [c for c in categories if c['id'] != category_id]

    if len(filtered) == len(categories):
        return jsonify({'error': 'Category not found'}), 404

    with open(path, 'w') as f:
        json.dump(filtered, f, indent=2)

    return jsonify({'message': 'Category deleted'}) 

@app.route('/update_tax', methods=['POST'])
def update_tax():
    service = request.form.get('service')
    try:
        cgst = float(request.form.get('cgst')) / 100 
        sgst = float(request.form.get('sgst')) / 100
    except (ValueError, TypeError):
        flash('Invalid input for tax rates.', 'error')
        return redirect(url_for('select_customer'))

    if os.path.exists(TAX_CONFIG_FILE):
        with open(TAX_CONFIG_FILE, 'r') as f:
            tax_data = json.load(f)
    else:
        tax_data = {}

    if service not in tax_data:
        tax_data[service] = {}

    tax_data[service]['cgst'] = cgst
    tax_data[service]['sgst'] = sgst

    with open(TAX_CONFIG_FILE, 'w') as f:
        json.dump(tax_data, f, indent=4)

    flash('Tax rates updated successfully.', 'success')
    return redirect(url_for('select_customer'))

@app.route('/shutdown', methods=['POST'])
def shutdown():
    print("🔴 Shutdown signal received from browser.")
    threading.Thread(target=lambda: os._exit(0)).start()  
    return 'Server shutting down...'

if __name__ == '__main__':
    import socket
    import errno
    
    debug_mode = "--debug" in sys.argv
    port = 7001
    
    # Check if port is already in use
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return False
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    return True
                raise
    
    if is_port_in_use(port):
        print(f"Port {port} is already in use!")
        print("Please stop the existing process or choose a different port.")
        sys.exit(1)
    
    print(f"Starting Flask app on http://127.0.0.1:{port}")
    
    try:
        # Try the standard Flask development server first
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,  # Always disable debug to avoid reloader issues
            use_reloader=False,
            use_debugger=False,
            threaded=True,
            processes=1
        )
    except OSError as e:
        if e.errno == 9:  # Bad file descriptor
            print("File descriptor error detected - using alternative server method...")
            
            # Fallback: Use Werkzeug server directly
            from werkzeug.serving import make_server, WSGIRequestHandler
            
            class QuietHandler(WSGIRequestHandler):
                def log_request(self, code='-', size='-'):
                    # Only log errors, not every request
                    if str(code).startswith('4') or str(code).startswith('5'):
                        super().log_request(code, size)
            
            try:
                server = make_server(
                    '127.0.0.1', 
                    port, 
                    app, 
                    threaded=True,
                    request_handler=QuietHandler
                )
                print(f"✅ Flask app running on http://127.0.0.1:{port}")
                print("Press Ctrl+C to quit")
                server.serve_forever()
            except Exception as fallback_error:
                print(f"Fallback method also failed: {fallback_error}")
                
                # Last resort: Basic threading approach
                import threading
                import time
                from werkzeug.serving import run_simple
                
                def run_app():
                    try:
                        run_simple(
                            '127.0.0.1', 
                            port, 
                            app, 
                            threaded=True, 
                            use_reloader=False,
                            use_debugger=False
                        )
                    except:
                        pass
                
                thread = threading.Thread(target=run_app, daemon=True)
                thread.start()
                
                print(f"✅ Flask app started on http://127.0.0.1:{port} (background thread)")
                try:
                    while thread.is_alive():
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutting down...")
                    sys.exit(0)
        else:
            # Re-raise other OSErrors
            raise
