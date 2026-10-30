from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pandas as pd
import os
import sqlite3
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pickle

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lifeflow_secret_key_2026_vijayawada_bloodbank'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'lifeflow.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ==================== MODELS ====================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='staff')  # admin, staff, donor
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(300))
    phone = db.Column(db.String(20))
    capacity_units = db.Column(db.Integer, default=300)
    is_24x7 = db.Column(db.String(10), default='Yes')
    components = db.Column(db.String(10), default='Yes')
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bag_id = db.Column(db.String(20), unique=True)
    branch_id = db.Column(db.Integer, default=1)
    blood_type = db.Column(db.String(5), nullable=False)
    quantity_ml = db.Column(db.Integer, default=450)
    collection_date = db.Column(db.String(20))
    expiry_date = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Available')
    donor_id = db.Column(db.String(20))

class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    blood_type = db.Column(db.String(5))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))
    address = db.Column(db.String(200))
    last_donation_date = db.Column(db.String(20))
    total_donations = db.Column(db.Integer, default=0)
    weight_kg = db.Column(db.Integer)
    hemoglobin = db.Column(db.Float)
    eligible = db.Column(db.String(10), default='Yes')

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.String(20), unique=True)
    donor_id = db.Column(db.String(20))
    donor_name = db.Column(db.String(100))
    blood_type = db.Column(db.String(5))
    appointment_date = db.Column(db.String(20))
    appointment_time = db.Column(db.String(10))
    purpose = db.Column(db.String(50), default='Donation')
    status = db.Column(db.String(20), default='Pending')
    branch_id = db.Column(db.Integer, default=1)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True)
    hospital_name = db.Column(db.String(150))
    blood_type = db.Column(db.String(5))
    units_requested = db.Column(db.Integer)
    order_date = db.Column(db.String(20))
    required_by = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Pending')
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    branch_id = db.Column(db.Integer, default=1)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== INIT DB & LOAD DATA ====================
def init_db():
    with app.app_context():
        db.create_all()
        # Create default admin
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@lifeflow.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin created: admin / admin123")

        # Load branches if empty
        if Branch.query.count() == 0:
            df = pd.read_csv('data/blood_bank_branches.csv')
            for _, row in df.iterrows():
                b = Branch(
                    id=row['branch_id'],
                    name=row['name'],
                    address=row['address'],
                    phone=row['phone'],
                    capacity_units=row['capacity_units'],
                    is_24x7=row['is_24x7'],
                    components=row['components'],
                    latitude=row['latitude'],
                    longitude=row['longitude']
                )
                db.session.add(b)
            db.session.commit()
            print("Branches loaded")

        # Load inventory
        if Inventory.query.count() == 0:
            df = pd.read_csv('data/inventory.csv')
            for _, row in df.iterrows():
                inv = Inventory(
                    bag_id=row['bag_id'],
                    branch_id=row['branch_id'],
                    blood_type=row['blood_type'],
                    quantity_ml=row['quantity_ml'],
                    collection_date=row['collection_date'],
                    expiry_date=row['expiry_date'],
                    status=row['status'],
                    donor_id=row['donor_id']
                )
                db.session.add(inv)
            db.session.commit()
            print("Inventory loaded")

        # Load donors
        if Donor.query.count() == 0:
            df = pd.read_csv('data/donors.csv')
            for _, row in df.iterrows():
                d = Donor(
                    donor_id=row['donor_id'],
                    name=row['name'],
                    age=row['age'],
                    gender=row['gender'],
                    blood_type=row['blood_type'],
                    phone=str(row['phone']),
                    email=row['email'],
                    address=row['address'],
                    last_donation_date=row['last_donation_date'],
                    total_donations=row['total_donations'],
                    weight_kg=row['weight_kg'],
                    hemoglobin=row['hemoglobin'],
                    eligible=row['eligible']
                )
                db.session.add(d)
            db.session.commit()
            print("Donors loaded")

        # Load appointments
        if Appointment.query.count() == 0:
            df = pd.read_csv('data/appointments.csv')
            for _, row in df.iterrows():
                a = Appointment(
                    appointment_id=row['appointment_id'],
                    donor_id=row['donor_id'],
                    donor_name=row['donor_name'],
                    blood_type=row['blood_type'],
                    appointment_date=row['appointment_date'],
                    appointment_time=row['appointment_time'],
                    purpose=row['purpose'],
                    status=row['status'],
                    branch_id=row['branch_id']
                )
                db.session.add(a)
            db.session.commit()
            print("Appointments loaded")

        # Load orders
        if Order.query.count() == 0:
            df = pd.read_csv('data/orders.csv')
            for _, row in df.iterrows():
                o = Order(
                    order_id=row['order_id'],
                    hospital_name=row['hospital_name'],
                    blood_type=row['blood_type'],
                    units_requested=row['units_requested'],
                    order_date=row['order_date'],
                    required_by=row['required_by'],
                    status=row['status'],
                    contact_person=row['contact_person'],
                    phone=str(row['phone']),
                    branch_id=row['branch_id']
                )
                db.session.add(o)
            db.session.commit()
            print("Orders loaded")

# Simple ML model for prediction (trained on synthetic RFM-like data)
def train_simple_model():
    # Synthetic training data based on classic blood donation RFM
    np.random.seed(42)
    n = 500
    recency = np.random.randint(0, 50, n)
    frequency = np.random.randint(1, 20, n)
    time = np.random.randint(2, 100, n)
    # Higher chance if low recency and high frequency
    prob = 1 / (1 + np.exp(0.1*recency - 0.3*frequency + 0.01*time - 1))
    y = (np.random.rand(n) < prob).astype(int)
    X = np.column_stack([recency, frequency, time])
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    with open('models/donation_predictor.pkl', 'wb') as f:
        pickle.dump(model, f)
    print("ML model trained and saved")

# ==================== ROUTES ====================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Welcome back to LifeFlow!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'staff')
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Stats
    total_branches = Branch.query.count()
    available_units = Inventory.query.filter_by(status='Available').count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    pending_appts = Appointment.query.filter_by(status='Pending').count()
    total_donors = Donor.query.count()
    
    # Blood type distribution for chart
    blood_counts = db.session.query(Inventory.blood_type, db.func.count(Inventory.id)).filter_by(status='Available').group_by(Inventory.blood_type).all()
    blood_labels = [b[0] for b in blood_counts]
    blood_values = [b[1] for b in blood_counts]
    
    return render_template('dashboard.html',
                           total_branches=total_branches,
                           available_units=available_units,
                           pending_orders=pending_orders,
                           pending_appts=pending_appts,
                           total_donors=total_donors,
                           blood_labels=blood_labels,
                           blood_values=blood_values)

@app.route('/capacity')
@login_required
def capacity():
    branches = Branch.query.all()
    inventory = Inventory.query.all()
    # Aggregate stock by type for main branch
    stock_by_type = db.session.query(Inventory.blood_type, db.func.count(Inventory.id)).filter(Inventory.status=='Available').group_by(Inventory.blood_type).all()
    search = request.args.get('search', '')
    if search:
        inventory = Inventory.query.filter(
            (Inventory.bag_id.contains(search)) |
            (Inventory.blood_type.contains(search)) |
            (Inventory.status.contains(search))
        ).all()
    return render_template('capacity.html', branches=branches, inventory=inventory, stock_by_type=stock_by_type, search=search)

@app.route('/appointments')
@login_required
def appointments():
    appts = Appointment.query.order_by(Appointment.appointment_date.desc()).all()
    donors = Donor.query.all()
    search = request.args.get('search', '')
    if search:
        appts = Appointment.query.filter(
            (Appointment.donor_name.contains(search)) |
            (Appointment.blood_type.contains(search)) |
            (Appointment.status.contains(search)) |
            (Appointment.appointment_id.contains(search))
        ).all()
    return render_template('appointments.html', appointments=appts, donors=donors, search=search)

@app.route('/orders')
@login_required
def orders():
    ords = Order.query.order_by(Order.order_date.desc()).all()
    search = request.args.get('search', '')
    if search:
        ords = Order.query.filter(
            (Order.hospital_name.contains(search)) |
            (Order.blood_type.contains(search)) |
            (Order.status.contains(search)) |
            (Order.order_id.contains(search))
        ).all()
    pending = Order.query.filter_by(status='Pending').count()
    completed = Order.query.filter_by(status='Completed').count()
    return render_template('orders.html', orders=ords, search=search, pending=pending, completed=completed)

@app.route('/donors')
@login_required
def donors_page():
    donors = Donor.query.all()
    search = request.args.get('search', '')
    if search:
        donors = Donor.query.filter(
            (Donor.name.contains(search)) |
            (Donor.blood_type.contains(search)) |
            (Donor.donor_id.contains(search)) |
            (Donor.phone.contains(search))
        ).all()
    return render_template('donors.html', donors=donors, search=search)

# CRUD for Inventory
@app.route('/inventory/add', methods=['POST'])
@login_required
def add_inventory():
    bag_id = request.form.get('bag_id')
    blood_type = request.form.get('blood_type')
    quantity_ml = request.form.get('quantity_ml', 450)
    status = request.form.get('status', 'Available')
    inv = Inventory(bag_id=bag_id, blood_type=blood_type, quantity_ml=quantity_ml, status=status,
                    collection_date=datetime.now().strftime('%Y-%m-%d'),
                    expiry_date=(datetime.now()+timedelta(days=42)).strftime('%Y-%m-%d'))
    db.session.add(inv)
    db.session.commit()
    flash('Blood bag added successfully', 'success')
    return redirect(url_for('capacity'))

@app.route('/inventory/delete/<int:id>')
@login_required
def delete_inventory(id):
    inv = Inventory.query.get_or_404(id)
    db.session.delete(inv)
    db.session.commit()
    flash('Record deleted', 'info')
    return redirect(url_for('capacity'))

@app.route('/inventory/update_status/<int:id>/<status>')
@login_required
def update_inventory_status(id, status):
    inv = Inventory.query.get_or_404(id)
    inv.status = status
    db.session.commit()
    flash(f'Status updated to {status}', 'success')
    return redirect(url_for('capacity'))

# CRUD Appointments
@app.route('/appointment/add', methods=['POST'])
@login_required
def add_appointment():
    appt = Appointment(
        appointment_id=f"AP{datetime.now().strftime('%H%M%S')}",
        donor_name=request.form.get('donor_name'),
        blood_type=request.form.get('blood_type'),
        appointment_date=request.form.get('appointment_date'),
        appointment_time=request.form.get('appointment_time'),
        purpose=request.form.get('purpose', 'Donation'),
        status='Pending'
    )
    db.session.add(appt)
    db.session.commit()
    flash('Appointment added', 'success')
    return redirect(url_for('appointments'))

@app.route('/appointment/update_status/<int:id>/<status>')
@login_required
def update_appointment_status(id, status):
    appt = Appointment.query.get_or_404(id)
    appt.status = status
    db.session.commit()
    flash(f'Appointment marked as {status}', 'success')
    return redirect(url_for('appointments'))

@app.route('/appointment/delete/<int:id>')
@login_required
def delete_appointment(id):
    appt = Appointment.query.get_or_404(id)
    db.session.delete(appt)
    db.session.commit()
    flash('Appointment deleted', 'info')
    return redirect(url_for('appointments'))

# CRUD Orders
@app.route('/order/add', methods=['POST'])
@login_required
def add_order():
    order = Order(
        order_id=f"ORD{datetime.now().strftime('%H%M%S')}",
        hospital_name=request.form.get('hospital_name'),
        blood_type=request.form.get('blood_type'),
        units_requested=int(request.form.get('units_requested', 1)),
        order_date=datetime.now().strftime('%Y-%m-%d'),
        required_by=request.form.get('required_by'),
        status='Pending',
        contact_person=request.form.get('contact_person'),
        phone=request.form.get('phone')
    )
    db.session.add(order)
    db.session.commit()
    flash('Order created', 'success')
    return redirect(url_for('orders'))

@app.route('/order/update_status/<int:id>/<status>')
@login_required
def update_order_status(id, status):
    order = Order.query.get_or_404(id)
    order.status = status
    db.session.commit()
    flash(f'Order marked as {status}', 'success')
    return redirect(url_for('orders'))

@app.route('/order/delete/<int:id>')
@login_required
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted', 'info')
    return redirect(url_for('orders'))

# Donor CRUD + Eligibility
@app.route('/donor/add', methods=['POST'])
@login_required
def add_donor():
    donor = Donor(
        donor_id=f"D{datetime.now().strftime('%H%M%S')}",
        name=request.form.get('name'),
        age=int(request.form.get('age', 25)),
        gender=request.form.get('gender'),
        blood_type=request.form.get('blood_type'),
        phone=request.form.get('phone'),
        email=request.form.get('email'),
        address=request.form.get('address'),
        weight_kg=int(request.form.get('weight_kg', 60)),
        hemoglobin=float(request.form.get('hemoglobin', 13.5)),
        total_donations=0,
        last_donation_date=datetime.now().strftime('%Y-%m-%d'),
        eligible='Yes'
    )
    # Auto eligibility
    if donor.age < 18 or donor.age > 65 or donor.weight_kg < 50 or donor.hemoglobin < 12.5:
        donor.eligible = 'No'
    db.session.add(donor)
    db.session.commit()
    flash('Donor added successfully', 'success')
    return redirect(url_for('donors_page'))

@app.route('/donor/delete/<int:id>')
@login_required
def delete_donor(id):
    d = Donor.query.get_or_404(id)
    db.session.delete(d)
    db.session.commit()
    flash('Donor deleted', 'info')
    return redirect(url_for('donors_page'))

@app.route('/eligibility', methods=['GET', 'POST'])
@login_required
def eligibility():
    result = None
    if request.method == 'POST':
        age = int(request.form.get('age', 0))
        weight = float(request.form.get('weight', 0))
        hb = float(request.form.get('hemoglobin', 0))
        last_donation = request.form.get('last_donation', '')
        gender = request.form.get('gender', 'Male')
        
        reasons = []
        eligible = True
        if age < 18 or age > 65:
            eligible = False
            reasons.append("Age must be between 18-65 years")
        if weight < 50:
            eligible = False
            reasons.append("Weight must be at least 50 kg")
        if hb < 12.5:
            eligible = False
            reasons.append("Hemoglobin must be ≥ 12.5 g/dL")
        if last_donation:
            try:
                last = datetime.strptime(last_donation, '%Y-%m-%d')
                days = (datetime.now() - last).days
                min_days = 90 if gender == 'Male' else 120
                if days < min_days:
                    eligible = False
                    reasons.append(f"Must wait at least {min_days} days since last donation (currently {days} days)")
            except:
                pass
        result = {'eligible': eligible, 'reasons': reasons}
    return render_template('eligibility.html', result=result)

@app.route('/prediction', methods=['GET', 'POST'])
@login_required
def prediction():
    result = None
    if request.method == 'POST':
        try:
            recency = float(request.form.get('recency', 5))
            frequency = float(request.form.get('frequency', 3))
            time = float(request.form.get('time', 24))
            with open('models/donation_predictor.pkl', 'rb') as f:
                model = pickle.load(f)
            X = np.array([[recency, frequency, time]])
            proba = model.predict_proba(X)[0][1]
            pred = model.predict(X)[0]
            result = {
                'probability': round(proba * 100, 1),
                'will_donate': bool(pred),
                'recency': recency,
                'frequency': frequency,
                'time': time
            }
        except Exception as e:
            flash(f'Prediction error: {str(e)}', 'danger')
    return render_template('prediction.html', result=result)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/donor_register', methods=['GET', 'POST'])
def donor_register():
    # Public donor registration form
    if request.method == 'POST':
        name = request.form.get('name')
        age = int(request.form.get('age', 25))
        gender = request.form.get('gender')
        blood_type = request.form.get('blood_type')
        phone = request.form.get('phone')
        email = request.form.get('email')
        weight = int(request.form.get('weight_kg', 60))
        hb = float(request.form.get('hemoglobin', 13.5))
        eligible = 'Yes'
        if age < 18 or age > 65 or weight < 50 or hb < 12.5:
            eligible = 'No'
        donor = Donor(
            donor_id=f"D{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=name, age=age, gender=gender, blood_type=blood_type,
            phone=phone, email=email, weight_kg=weight, hemoglobin=hb,
            address=request.form.get('address', 'Vijayawada'),
            total_donations=0, eligible=eligible,
            last_donation_date=datetime.now().strftime('%Y-%m-%d')
        )
        db.session.add(donor)
        db.session.commit()
        flash(f'Thank you {name}! You are registered. Eligibility: {eligible}', 'success')
        return redirect(url_for('donor_register'))
    return render_template('donor_register.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Admin access only', 'danger')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    stats = {
        'users': User.query.count(),
        'branches': Branch.query.count(),
        'inventory': Inventory.query.count(),
        'donors': Donor.query.count(),
        'appointments': Appointment.query.count(),
        'orders': Order.query.count()
    }
    return render_template('admin.html', users=users, stats=stats)

if __name__ == '__main__':
    os.makedirs('models', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    init_db()
    train_simple_model()
    app.run(debug=True, host='0.0.0.0', port=5001)
