import os

# 1. Define the project structure and content
project_structure = {
    "requirements.txt": """flask==3.0.3
flask-jwt-extended==4.6.0
PyJWT==2.8.0""",

    "database.py": """import sqlite3

def init_db():
    conn = sqlite3.connect('sdsmclf.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            customer_name TEXT,
            customer_id TEXT,
            meter_id TEXT,
            amount REAL,
            token TEXT,
            status TEXT,
            gateway_verification TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meter_states (
            meter_id TEXT PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO meter_states (meter_id, balance) VALUES ('SM4509876', 0.0)")
    conn.commit()
    conn.close()

def log_transaction(customer_name, customer_id, meter_id, amount, token, status, verification_msg):
    conn = sqlite3.connect('sdsmclf.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO audit_logs (customer_name, customer_id, meter_id, amount, token, status, gateway_verification)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (customer_name, customer_id, meter_id, amount, token, status, verification_msg))
    conn.commit()
    conn.close()

def update_meter_db(meter_id, new_balance):
    conn = sqlite3.connect('sdsmclf.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE meter_states SET balance = ? WHERE meter_id = ?', (new_balance, meter_id))
    conn.commit()
    conn.close()

def get_audit_logs():
    conn = sqlite3.connect('sdsmclf.db')
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, customer_name, meter_id, amount, token, status, gateway_verification FROM audit_logs ORDER BY id DESC")
    logs = cursor.fetchall()
    conn.close()
    return logs
""",

    "security.py": """import jwt
import datetime

SECRET_KEY = "sdsmclf_super_secure_secret_key_v1"

class SecurityEngine:
    @staticmethod
    def generate_secure_token(customer_id, meter_id, amount):
        payload = {
            "cid": customer_id,
            "mid": meter_id,
            "amt": amount,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    @staticmethod
    def validate_token(token):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return {"valid": True, "payload": payload}
        except jwt.ExpiredSignatureError:
            return {"valid": False, "reason": "Token has expired."}
        except jwt.InvalidTokenError:
            return {"valid": False, "reason": "Token signature tampered or invalid."}
""",

    "smart_meter.py": """import sqlite3
from database import update_meter_db

class SmartMeter:
    def __init__(self, meter_id):
        self.meter_id = meter_id
        self.balance = self._load_current_balance()

    def _load_current_balance(self):
        conn = sqlite3.connect('sdsmclf.db')
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM meter_states WHERE meter_id = ?", (self.meter_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0.0

    def load_credit(self, amount):
        self.balance += amount
        update_meter_db(self.meter_id, self.balance)
        return {"meter_id": self.meter_id, "new_balance": self.balance, "status": "ACTIVE"}
""",

    "app.py": """from flask import Flask, render_template, request, jsonify
from database import init_db, log_transaction, get_audit_logs
from security import SecurityEngine
from smart_meter import SmartMeter

app = Flask(__name__)
init_db()

@app.route('/')
def dashboard():
    logs = get_audit_logs()
    formatted_logs = [{"timestamp": l[0], "customer": l[1], "meter": l[2], "amount": l[3], "token": l[4][:20] + "...", "status": l[5], "verification": l[6]} for l in logs]
    return render_template('dashboard.html', logs=formatted_logs)

@app.route('/api/v1/purchase', methods=['POST'])
def purchase_credit():
    data = request.json
    customer_name = data.get('customer_name', 'Musa Adewale')
    customer_id = data.get('customer_id', 'IB001245')
    meter_id = data.get('meter_id', 'SM4509876')
    amount = float(data.get('amount', 0))

    gateway_verified = "PAYMENT_SUCCESS_BANK_APPROVED"
    secure_token = SecurityEngine.generate_secure_token(customer_id, meter_id, amount)
    validation_check = SecurityEngine.validate_token(secure_token)
    
    if validation_check["valid"]:
        meter = SmartMeter(meter_id)
        meter_response = meter.load_credit(amount)
        log_transaction(customer_name, customer_id, meter_id, amount, secure_token, "SUCCESS", gateway_verified)
        return jsonify({"status": "SUCCESS", "message": f"Credit loaded successfully. Balance: ₦{meter_response['new_balance']}", "token_signature": secure_token, "meter_status": meter_response}), 200
    return jsonify({"status": "FAILED", "message": validation_check["reason"]}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
""",

    "templates/dashboard.html": """<!DOCTYPE html>
<html>
<head>
    <title>SDSMCLF v1.0 Presentation Dashboard</title>
    <style>
        body { font-family: sans-serif; background: #f4f6f9; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { background: #1e3a8a; color: white; padding: 15px; border-radius: 8px; text-align: center; }
        .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 20px; margin-top: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        input { width: 90%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #10b981; color: white; border: none; padding: 12px; width: 95%; border-radius: 4px; font-weight: bold; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; border-bottom: 1px solid #ddd; text-align: left; font-size: 13px; }
        th { background: #f3f4f6; }
        .console { background: #111827; color: #10b981; padding: 15px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; margin-top: 15px; }
    </style>
</head>
<body>
<div class="container">
    <header><h2>SDSMCLF v1.0 Working Prototype</h2><p>Live Seminar Simulation Interface</p></header>
    <div class="grid">
        <div class="card">
            <h3>Execute Demo Transaction</h3>
            <input type="text" id="custName" value="Musa Adewale">
            <input type="text" id="custId" value="IB001245">
            <input type="text" id="meterId" value="SM4509876">
            <input type="number" id="amount" value="5000">
            <button onclick="triggerPipeline()">Send Secure Request</button>
            <div class="console" id="consoleLogs">> Ready for demonstration...</div>
        </div>
        <div class="card">
            <h3>Real-Time Immutable Audit Log Repository</h3>
            <table>
                <thead><tr><th>Timestamp</th><th>Customer</th><th>Meter ID</th><th>Value</th><th>Verification</th><th>Status</th></tr></thead>
                <tbody>
                    {% for log in logs %}
                    <tr><td>{{ log.timestamp }}</td><td>{{ log.customer }}</td><td>{{ log.meter }}</td><td>₦{{ log.amount }}</td><td>{{ log.verification }}</td><td>{{ log.status }}</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
<script>
    async function triggerPipeline() {
        const consoleLogs = document.getElementById('consoleLogs');
        consoleLogs.innerHTML = "> Connecting to simulated Payment Gateway...\\n";
        const payload = {
            customer_name: document.getElementById('custName').value,
            customer_id: document.getElementById('custId').value,
            meter_id: document.getElementById('meterId').value,
            amount: document.getElementById('amount').value
        };
        try {
            const response = await fetch('/api/v1/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (response.ok) {
                consoleLogs.innerHTML += `> Gateway Handshake verified: APPROVED\\n> JWT Token Engine signed payload.\\n> RESPONSE: ${data.message}\\n`;
                setTimeout(() => { window.location.reload(); }, 2000);
            }
        } catch (err) { consoleLogs.innerHTML += `> Error: ${err.message}\\n`; }
    }
</script>
</body>
</html>"""
}

# 2. Automatically generate the files locally
print("🚀 Starting SDSMCLF v1.0 Automatic Project Generation...")
os.makedirs("templates", exist_ok=True)

for path, content in project_structure.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(file=None) # Cleans log presentation track

print("✅ All files created successfully in your directory!")
print("👉 Next step: Run 'pip install -r requirements.txt' then 'python app.py' to launch.")
