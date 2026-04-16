from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__, template_folder="template")


# إنشاء قاعدة بيانات (لو مش موجودة)
def init_db():
    conn = sqlite3.connect("bakery.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL
    )
    """)
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template("test.html")

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name']
    price = request.form['price']
    stock = request.form['stock']
    
    conn = sqlite3.connect("bakery.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", (name, price, stock))
    conn.commit()
    conn.close()
    
    return f"تمت إضافة المنتج: {name}!"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
