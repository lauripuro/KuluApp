from flask import Flask, request, render_template, redirect
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payer TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Routes

@app.route('/')
def index():
    return render_template('submit.html')


@app.route('/submit', methods=['POST'])
def submit():
    payer = request.form['payer']
    amount = float(request.form['amount'])
    category = request.form['category']
    date = datetime.now().strftime('%Y-%m-%d')

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('INSERT INTO expenses (payer, amount, category, date) VALUES (?, ?, ?, ?)',
              (payer, amount, category, date))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/search', methods=['GET', 'POST'])
def search():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    # Default empty values
    start_date = end_date = payer = category = ''

    if request.method == 'POST':
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        payer = request.form.get('payer', '')
        category = request.form.get('category', '')

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        if payer:
            query += " AND payer = ?"
            params.append(payer)
        if category:
            query += " AND category = ?"
            params.append(category)

    query += " ORDER BY date DESC, id DESC LIMIT 20"
    c.execute(query, params)
    results = c.fetchall()

    # Filtered total
    total_amount = sum(row[2] for row in results)

    # Unfiltered for balance
    c.execute("SELECT payer, amount FROM expenses")
    all_data = c.fetchall()
    conn.close()

    siiri_sum = sum(row[1] for row in all_data if row[0] == 'Siiri')
    lauri_sum = sum(row[1] for row in all_data if row[0] == 'Lauri')
    half = (siiri_sum + lauri_sum) / 2
    balance = round(half - siiri_sum, 2)

    return render_template(
        'search.html',
        results=results,
        total_amount=total_amount,
        siiri_sum=siiri_sum,
        lauri_sum=lauri_sum,
        balance=balance,
        start_date=start_date,
        end_date=end_date,
        payer=payer,
        category=category
    )



@app.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    date = request.form['date']
    payer = request.form['payer']
    category = request.form['category']
    amount = request.form['amount']

    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        UPDATE expenses SET date = ?, payer = ?, category = ?, amount = ? WHERE id = ?
    ''', (date, payer, category, amount, id))
    conn.commit()
    conn.close()
    return redirect('/search')

if __name__ == '__main__':
    app.run(debug=True)
