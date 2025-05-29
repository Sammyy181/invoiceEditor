from flask import Flask, render_template, request, redirect, url_for, session
from update_excel import get_services, get_customers, update_customer_info, get_customer_info, add_customer_info

app = Flask(__name__)
app.secret_key = 'your-secret-key'

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

@app.route('/select_customer', methods=['GET', 'POST'])
def select_customer():
    service = session.get('service')
    customers = get_customers(service)

    if request.method == 'POST':
        if request.form.get('action') == 'add_new':
            # This just re-renders the page with the popup showing
            return render_template('select_customer.html', customers=customers, service=service, show_popup=True)
        else:
            session['customer'] = request.form['customer']
            return redirect(url_for('update_customer'))

    return render_template('select_customer.html', customers=customers, service=service, show_popup=False)

@app.route('/add_customer', methods=['POST'])
def add_customer():
    service = session.get(service)
    
    name = request.form['customer_name']
    price = float(request.form['unit_price'])
    period = request.form['consumption_period']
    usage = float(request.form['usage_percent'])

    # Call helper function
    add_customer_info(service, name, price, period, usage)

    return redirect(url_for('select_customer'))


@app.route('/update_customer', methods=['GET', 'POST'])
def update_customer():
    if request.method == 'POST':
        updates = {k: v for k, v in request.form.items() if v.strip() != ''}
        update_customer_info(session['service'], session['customer'], updates)
        return redirect(url_for('thank_you'))

    # Use helper function from backend tools
    current_values = get_customer_info(session['service'], session['customer'])

    return render_template('update_customer.html', current=current_values)


@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/submit', methods=['POST'])
def submit():
    service = request.form['service']
    customer = request.form['customer']
    usage = request.form.get('Usage (%)', '').strip()
    total_cost = request.form.get('Total Cost', '').strip()
    remarks = request.form.get('Remarks', '').strip()

    updates = {
        'Usage (%)': usage,
        'Total Cost': total_cost,
        'Remarks': remarks
    }

    print(f"\nForm received for {customer} under {service}:")
    print(updates)

    update_customer_info(service, customer, updates)
    return render_template('thank_you.html')
