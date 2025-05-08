from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import datetime
import secrets
import requests
import hashlib
from utils.logger import setup_logger, log_activity, log_attack_attempt
import socket
import csv

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.secret_key = secrets.token_hex(16)

# Setup loggers
access_logger = setup_logger('access_log', os.path.join('..', 'logs', 'access.log'))
error_logger = setup_logger('error_log', os.path.join('..', 'logs', 'error.log'))
attack_logger = setup_logger('attack_log', os.path.join('..', 'logs', 'attack.log'))
honeypot_logger = setup_logger('honeypot_log', os.path.join('..', 'logs', 'honeypot.log'))

# Dummy user data for demonstration
users = {
    "admin": {
        "password": "admin",  # Intentionally weak password
        "role": "Administrator",
        "email": "admin@medisecure.example",
        "department": "Administration"
    },
    "doctor": {
        "password": "doctor123",
        "role": "Doctor",
        "email": "doctor@medisecure.example",
        "department": "Cardiology"
    },
    "nurse": {
        "password": "nurse123",
        "role": "Nurse",
        "email": "nurse@medisecure.example",
        "department": "Emergency"
    }
}

# Honeypot traps - sensitive endpoints that should never be accessed
honeypot_endpoints = [
    '/admin/backup',
    '/api/v1/users/all',
    '/system/config',
    '/logs/view',
    '/api/v1/analytics/reports'
]

@app.before_request
def log_request():
    """Log every request to the system"""
    # Skip logging for static resources
    if not request.path.startswith('/static/'):
        log_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'ip': request.remote_addr,
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('User-Agent', ''),
            'referrer': request.referrer,
            'query_params': dict(request.args),
            'form_data': dict(request.form),
            'cookies': dict(request.cookies),
            'headers': dict(request.headers),
            'is_xhr': request.headers.get('X-Requested-With') == 'XMLHttpRequest',  # Fixed line
            'content_length': request.content_length,
            'content_type': request.content_type,
            'user': session.get('username', 'anonymous')
        }
        
        # Check if this is a potential attack
        is_attack = False
        attack_type = None
        
        # Check for SQL injection attempts
        sql_patterns = ["'", "UNION", "SELECT", "DROP", "INSERT", "DELETE", "UPDATE", "--", "1=1"]
        for pattern in sql_patterns:
            if pattern in request.path or pattern in str(request.args) or pattern in str(request.form):
                is_attack = True
                attack_type = "SQL Injection"
                break
                
        # Check for XSS attempts
        xss_patterns = ["<script>", "javascript:", "onerror=", "onload=", "eval("]
        for pattern in xss_patterns:
            if pattern in request.path or pattern in str(request.args) or pattern in str(request.form):
                is_attack = True
                attack_type = "XSS"
                break
                
        # Check for path traversal
        if "../" in request.path or "..\\" in request.path:
            is_attack = True
            attack_type = "Path Traversal"
            
        # Check for honeypot traps
        if request.path in honeypot_endpoints:
            is_attack = True
            attack_type = "Honeypot Trap"
            honeypot_logger.warning(f"Honeypot trap triggered: {request.path} by {request.remote_addr}")
            
        # Log appropriately
        if is_attack:
            log_data['attack_type'] = attack_type
            log_attack_attempt(attack_logger, log_data)
        else:
            log_activity(access_logger, log_data)

@app.route('/')
def index():
    return render_template('index.html')

USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.csv')

def load_users():
    users = []
    with open(USERS_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            users.append(row)
    return users

def find_user(username):
    users = load_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = find_user(username)
        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            session['user_id'] = username
            log_activity(access_logger, {
                'event': 'login_success',
                'username': username,
                'ip': request.remote_addr
            })
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'
            log_activity(access_logger, {
                'event': 'login_failure',
                'attempted_username': username,
                'ip': request.remote_addr
            })
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    if 'username' in session:
        log_activity(access_logger, {
            'event': 'logout',
            'username': session['username'],
            'ip': request.remote_addr
        })
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/reports')
def reports():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('reports.html')

@app.route('/users')
def users_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('users.html')

@app.route('/settings')
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

# API endpoints (intentionally vulnerable)
@app.route('/api/v1/user/<username>', methods=['GET'])
def get_user(username):
    if username in users:
        # Intentionally returning sensitive data without proper authentication
        return jsonify(users[username])
    return jsonify({"error": "User not found"}), 404

@app.route('/api/v1/search', methods=['GET'])
def search_api():
    """Intentionally vulnerable search API with SQL injection"""
    query = request.args.get('q', '')
    
    # Log the search query
    log_activity(access_logger, {
        'event': 'search_query',
        'query': query,
        'ip': request.remote_addr
    })
    
    # Fake search results
    results = [
        {"id": 1, "name": "John Smith", "ssn": "123-45-6789", "dob": "1980-01-15"},
        {"id": 2, "name": "Jane Doe", "ssn": "987-65-4321", "dob": "1975-06-22"},
        {"id": 3, "name": "Robert Johnson", "ssn": "456-78-9012", "dob": "1990-03-30"}
    ]
    
    # Return results
    return jsonify({"query": query, "results": results})

@app.route('/upload', methods=['GET', 'POST'])
def file_upload():
    """Intentionally vulnerable file upload"""
    if 'username' not in session:
        return redirect(url_for('login'))
        
    message = None
    
    if request.method == 'POST':
        if 'file' not in request.files:
            message = "No file part"
        else:
            file = request.files['file']
            if file.filename == '':
                message = "No selected file"
            else:
                # Intentionally vulnerable - no validation of file type or content
                filename = file.filename
                file_path = os.path.join('uploads', filename)
                os.makedirs('uploads', exist_ok=True)
                file.save(file_path)
                message = f"File {filename} uploaded successfully"
                
                # Log the upload
                log_activity(access_logger, {
                    'event': 'file_upload',
                    'filename': filename,
                    'ip': request.remote_addr
                })
                
    return render_template('upload.html', message=message)

@app.route('/api/v1/analytics/reports', methods=['GET'])
def analytics_reports():
    # This is a honeypot endpoint
    api_key = request.args.get('key')
    period = request.args.get('period', '30days')
    
    log_attack_attempt(attack_logger, {
        'event': 'honeypot_api_access',
        'endpoint': '/api/v1/analytics/reports',
        'api_key': api_key,
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', '')
    })
    
    # Return fake data to make it look legitimate
    return jsonify({
        "status": "success",
        "data": {
            "total_reports": 156,
            "by_type": {
                "health_summary": 78,
                "medication_history": 42,
                "lab_results": 36
            },
            "by_doctor": {
                "Dr. Williams": 52,
                "Dr. Johnson": 48,
                "Dr. Smith": 56
            }
        }
    })

# Add a vulnerable SQL injection endpoint
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'patients.csv')

def load_patients():
    patients = []
    with open(DATA_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row['age'] = int(row['age'])
            patients.append(row)
    return patients

def save_patients(patients):
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'name', 'age', 'condition', 'ssn']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for patient in patients:
            writer.writerow(patient)

@app.route('/patient/search', methods=['GET'])
def patient_search():
    if 'username' not in session:
        return redirect(url_for('login'))
    query = request.args.get('q', '')
    log_activity(access_logger, {
        'event': 'patient_search',
        'query': query,
        'ip': request.remote_addr
    })
    patients = load_patients()
    if query:
        filtered_patients = []
        for patient in patients:
            if (
                query.lower() in patient["name"].lower()
                or query.lower() in patient["condition"].lower()
                or query.lower() in patient["id"].lower()
                or query.lower() in patient["ssn"].lower()
                or query.lower() in str(patient["age"])
            ):
                filtered_patients.append(patient)
        patients = filtered_patients
    return render_template('patient_search.html', patients=patients, query=query)

@app.route('/patient/<patient_id>/view')
def view_patient(patient_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    patients = load_patients()
    patient = next((p for p in patients if p["id"] == patient_id), None)
    if not patient:
        return "Patient not found", 404
    return render_template('view_patient.html', patient=patient)

@app.route('/patient/<patient_id>/edit', methods=['GET', 'POST'])
def edit_patient(patient_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    patients = load_patients()
    patient = next((p for p in patients if p["id"] == patient_id), None)
    if not patient:
        return "Patient not found", 404
    if request.method == 'POST':
        patient['name'] = request.form.get('name', patient['name'])
        patient['age'] = int(request.form.get('age', patient['age']))
        patient['condition'] = request.form.get('condition', patient['condition'])
        save_patients(patients)
        return redirect(url_for('patient_search'))
    return render_template('edit_patient.html', patient=patient)

@app.route('/patient/<patient_id>/delete')
def delete_patient(patient_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    patients = load_patients()
    patients = [p for p in patients if p["id"] != patient_id]
    save_patients(patients)
    return redirect(url_for('patient_search'))

if __name__ == '__main__':
    # Ensure log directory exists
    os.makedirs(os.path.join('..', 'logs'), exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)