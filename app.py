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

    if request.method == 'POST':
        date = request.form['date']
        payer = request.form['payer']
        category = request.form['category']

        if date:
            query += " AND date = ?"
            params.append(date)
        if payer:
            query += " AND payer = ?"
            params.append(payer)
        if category:
            query += " AND category = ?"
            params.append(category)

    # Add sorting and limit
    query += " ORDER BY date DESC, id DESC LIMIT 20"

    c.execute(query, params)
    results = c.fetchall()
    conn.close()
    return render_template('search.html', results=results)

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