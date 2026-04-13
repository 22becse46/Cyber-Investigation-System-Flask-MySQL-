from flask import Flask, render_template, request, redirect, session
from db import get_connection

app = Flask(__name__)
app.secret_key = "secret123"

# 🔐 Login Page
@app.route('/')
def login():
    return render_template("login.html")


# 🔐 Login Logic
@app.route('/login_user', methods=['POST'])
def login_user():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    username = request.form['username']
    password = request.form['password']

    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user:
        session['user'] = username
        return redirect('/dashboard')
    else:
        return "❌ Invalid Credentials"


# 🖥 Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template("dashboard.html")


# 🔍 Search Page
@app.route('/search')
def search_page():
    if 'user' not in session:
        return redirect('/')
    return render_template("search.html")


# 🔍 Search Logic
@app.route('/search_record', methods=['POST'])
def search_record():
    if 'user' not in session:
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    keyword = request.form['keyword']
    
    # 🧾 Save Search History
    cursor.execute(
    "INSERT INTO search_logs (username, keyword) VALUES (%s, %s)",
    (session['user'], keyword)
    )
    conn.commit()

    query = """
    SELECT * FROM records
    WHERE mobile = %s
    OR aadhaar = %s
    OR name LIKE %s
    OR father_name LIKE %s
    OR email LIKE %s
    OR address LIKE %s
    """

    values = (
        keyword, keyword,
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    )

    cursor.execute(query, values)
    results = cursor.fetchall()

    # 🔐 Aadhaar Masking
    for row in results:
        if row['aadhaar'] and len(row['aadhaar']) >= 4:
            row['aadhaar'] = "XXXX-XXXX-" + row['aadhaar'][-4:]

    cursor.close()
    conn.close()

    return render_template("results.html", data=results)


# ➕ Add Record Page
@app.route('/add')
def add_page():
    if 'user' not in session:
        return redirect('/')
    return render_template("add_record.html")


# 💾 Save Record
@app.route('/add_record', methods=['POST'])
def add_record():
    if 'user' not in session:
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()

    name = request.form['name']
    father_name = request.form['father_name']
    mobile = request.form['mobile']
    email = request.form['email']
    aadhaar = request.form['aadhaar']
    address = request.form['address']

    # 🔍 Basic Validation
    if not mobile.isdigit():
        return "❌ Mobile must be numeric"

    query = """
    INSERT INTO records (name, father_name, mobile, email, aadhaar, address)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = (name, father_name, mobile, email, aadhaar, address)

    cursor.execute(query, values)
    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/dashboard')   # ✅ better UX


# 🚪 Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ✅ ALWAYS LAST
if __name__ == '__main__':
    app.run(debug=True)
    
    
    # 📜 View Search History
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM search_logs ORDER BY search_time DESC")
    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("history.html", data=logs)