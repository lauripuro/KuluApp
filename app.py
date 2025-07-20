from flask import Flask, request, render_template, redirect
from datetime import datetime
import psycopg
import os

app = Flask(__name__)

# Connect to PostgreSQL using env variable
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable not set")
    return psycopg.connect(database_url, sslmode='require')

# Initialize database
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            payer TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# Home (Submit form)
@app.route('/')
def index():
    return render_template('submit.html')

# Submit expense
@app.route('/submit', methods=['POST'])
def submit():
    payer = request.form['payer']
    amount = float(request.form['amount'])
    category = request.form['category']
    date = datetime.now().strftime('%Y-%m-%d')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO expenses (payer, amount, category, date)
        VALUES (%s, %s, %s, %s)
    ''', (payer, amount, category, date))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

# Search & filter
@app.route('/search', methods=['GET', 'POST'])
def search():
    conn = get_db_connection()
    cur = conn.cursor()

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    # Defaults for form fields
    date = ''
    start_date = ''
    end_date = ''
    payer = ''
    category = ''

    if request.method == 'POST':
        date = request.form.get('date', '')
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        payer = request.form.get('payer', '')
        category = request.form.get('category', '')

        if date:
            query += " AND date = %s"
            params.append(date)
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
        if payer:
            query += " AND payer = %s"
            params.append(payer)
        if category:
            query += " AND category = %s"
            params.append(category)

    query += " ORDER BY date DESC LIMIT 20"

    cur.execute(query, params)
    results = cur.fetchall()

    # Shared expenses overview
    cur.execute("SELECT SUM(amount) FROM expenses WHERE payer = 'Siiri'")
    siiri_sum = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(amount) FROM expenses WHERE payer = 'Lauri'")
    lauri_sum = cur.fetchone()[0] or 0
    balance = siiri_sum - lauri_sum

    # Total filtered amount
    total_amount = sum(row[2] for row in results)

    cur.close()
    conn.close()

    return render_template(
        'search.html',
        results=results,
        total_amount=total_amount,
        siiri_sum=siiri_sum,
        lauri_sum=lauri_sum,
        balance=balance,
        date=date,
        start_date=start_date,
        end_date=end_date,
        payer=payer,
        category=category
    )

# Edit a row
@app.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    date = request.form['date']
    payer = request.form['payer']
    category = request.form['category']
    amount = float(request.form['amount'])

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE expenses
        SET date = %s, payer = %s, category = %s, amount = %s
        WHERE id = %s
    ''', (date, payer, category, amount, id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/search')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
