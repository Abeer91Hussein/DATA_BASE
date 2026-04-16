from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import uuid

app = Flask(__name__)
app.secret_key = "secret123"

#database connection
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="abeer@122S",
        database="salehkhalaf"
    )

#route for the main bage 
@app.route('/')
def home():
    return render_template('test.html')

#route for employee_login bage 
@app.route('/employee', methods=['GET', 'POST'])
def employee():
    error = None
    if request.method == 'POST':
        eid = request.form['employee_id']
        pw = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT employee_id FROM Employee WHERE employee_id=%s AND password=%s",
            (eid, pw)
        )
        emp = cursor.fetchone()
        cursor.close()
        db.close()

        if emp:
            session['employee_id'] = eid
            return redirect(url_for('employee_portal'))
        else:
            error = "Invalid Employee ID or Password"

    return render_template('employee_login.html', error=error)

#route for employee_login  portal bage 
@app.route('/employee_portal')
def employee_portal():
    if 'employee_id' not in session:
        return redirect(url_for('employee'))
    return render_template('employee_login.html')

#route for _login bage 
@app.route('/manager', methods=['GET', 'POST'])
def manager():
    error = None
    if request.method == 'POST':
        mid = request.form['manager_id']
        pw = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT manager_id FROM Manager WHERE manager_id=%s AND password=%s",
            (mid, pw)
        )
        mgr = cursor.fetchone()
        cursor.close()
        db.close()

        if mgr:
            session['manager_id'] = mid
            return redirect(url_for('manager_portal'))
        else:
            error = "Invalid Manager ID or Password"

    return render_template('manager_login.html', error=error)


@app.route('/manager_portal')
def manager_portal():
    if 'manager_id' not in session:
        return redirect(url_for('manager'))
    return render_template('manager_login.html')



# ---------- CUSTOMER LOGIN ----------
@app.route('/customer', methods=['GET', 'POST'])
def customer():
    error = None
    if request.method == 'POST':
        cid = request.form['customer_id']
        pw = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT customer_id FROM Customer WHERE customer_id=%s AND password=%s",
            (cid, pw)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session['customer_id'] = cid
            return redirect(url_for('customer_portal'))
        else:
            error = "Invalid Customer ID or Password"

    return render_template('customer.html', error=error)

# ---------- LOGOUT ----------
@app.route('/customer_logout')
def customer_logout():
    session.clear()
    return redirect(url_for('customer'))

# ---------- DASHBOARD ----------
@app.route('/customer_portal')
def customer_portal():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))
    return render_template('customer_login.html')

# ---------- PRODUCTS ----------
@app.route('/customer_products')
def customer_products():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT product_id, product_name, price
        FROM Product
        WHERE product_status='available'
    """)
    products = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('customer_products.html', products=products)
# ---------- ADD TO CART ----------
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])

    db = get_db()
    cursor = db.cursor()

    # تحقق من وجود الكارت أو إنشاء واحد جديد
    cursor.execute("SELECT cart_id FROM Cart WHERE customer_id=%s", (customer_id,))
    cart = cursor.fetchone()

    if not cart:
        cursor.execute(
            "INSERT INTO Cart (customer_id, creation_time) VALUES (%s, NOW())",
            (customer_id,)
        )
        cart_id = cursor.lastrowid
    else:
        cart_id = cart[0]

    # تحقق من وجود المنتج في الكارت
    cursor.execute("""
        SELECT quantity FROM cart_product
        WHERE cart_id=%s AND product_id=%s
    """, (cart_id, product_id))
    item = cursor.fetchone()

    if item:
        cursor.execute("""
            UPDATE cart_product
            SET quantity = quantity + %s
            WHERE cart_id=%s AND product_id=%s
        """, (quantity, cart_id, product_id))
    else:
        cursor.execute("""
            INSERT INTO cart_product (cart_id, product_id, quantity)
            VALUES (%s, %s, %s)
        """, (cart_id, product_id, quantity))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('customer_cart'))


# ---------- VIEW CART ----------
@app.route('/customer_cart')
def customer_cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # تعديل: SELECT مع حساب total لكل منتج
    cursor.execute("""
        SELECT 
            p.product_id,
            p.product_name,
            p.price,
            cp.quantity,
            (p.price * cp.quantity) AS total
        FROM Cart c
        JOIN cart_product cp ON c.cart_id = cp.cart_id
        JOIN Product p ON cp.product_id = p.product_id
        WHERE c.customer_id = %s
    """, (customer_id,))

    cart_items = cursor.fetchall()
    total_price = sum(item['total'] for item in cart_items)

    cursor.close()
    db.close()

    return render_template(
        'customer_cart.html',
        cart_items=cart_items,
        total_price=total_price
    )


# ---------- REMOVE FROM CART ----------
@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']
    product_id = request.form['product_id']

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        DELETE cp FROM cart_product cp
        JOIN Cart c ON cp.cart_id = c.cart_id
        WHERE c.customer_id = %s AND cp.product_id = %s
    """, (customer_id, product_id))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('customer_cart'))

# ---------- CHECKOUT ----------
@app.route('/checkout', methods=['POST'])
def checkout():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']
    invoice_id = str(uuid.uuid4())[:8]

    db = get_db()
    cursor = db.cursor()

    try:
        # 🔒 ابدأ transaction
        db.start_transaction()

        # 1️⃣ الحصول على cart_id مع قفل الصف
        cursor.execute("""
            SELECT cart_id
            FROM Cart
            WHERE customer_id = %s
            FOR UPDATE
        """, (customer_id,))
        cart = cursor.fetchone()

        if not cart:
            db.rollback()
            return redirect(url_for('customer_cart'))

        cart_id = cart[0]
        db.commit()

        # 2️⃣ إنشاء الفاتورة
        cursor.execute("""
            INSERT INTO Sales_invoice
            (invoice_id, customer_id, branch_id, invoice_date, payment_method)
            VALUES (%s, %s, 1, NOW(), 'CASH/ONARRIVAL')
        """, (invoice_id, customer_id))
        db.commit()

        # 3️⃣ نقل المنتجات من الكارت للفاتورة
        cursor.execute("""
            INSERT INTO invoice_product (invoice_id, product_id, quantity)
            SELECT %s, product_id, quantity
            FROM cart_product
            WHERE cart_id = %s
        """, (invoice_id, cart_id))

        cursor.execute("""  
        update Product p
         inner join cart_product cp ON p.product_id = cp.product_id
         inner join Cart c ON cp.cart_id = c.cart_id
	set p.available_quantity = p.available_quantity - cp.quantity
        where c.customer_id = %s
        """,(customer_id,))

        # 4️⃣ تفريغ الكارت
        cursor.execute("""
            DELETE FROM cart_product
            WHERE cart_id = %s
        """, (cart_id,))
            
        # ✅ إنهاء العملية بنجاح
        db.commit()

    except Exception as e:
        db.rollback()
        return f"Checkout Error: {str(e)}", 500
    
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('customer_invoice', invoice_id=invoice_id))

# ---------- INVOICE ----------
@app.route('/customer_invoice/<invoice_id>')
def customer_invoice(invoice_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.product_name, p.price, ip.quantity,
               (p.price * ip.quantity) AS total
        FROM invoice_product ip
        JOIN Product p ON ip.product_id = p.product_id
        WHERE ip.invoice_id=%s
    """, (invoice_id,))

    items = cursor.fetchall()
    total = sum(i['total'] for i in items)

    cursor.close()
    db.close()

    return render_template(
        'customer_invoice.html',
        cart_items=items,
        total_price=total
    )

@app.route('/customer_signup', methods=['GET', 'POST'])
def customer_signup():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        name = request.form['name']
        phone = request.form['phone']
        address = request.form['address']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # نجيب person_id جديد
            cursor.execute("SELECT IFNULL(MAX(person_id), 0) + 1 AS new_id FROM Person")
            person_id = cursor.fetchone()['new_id']

            # إدخال في Person
            cursor.execute("""
                INSERT INTO Person (person_id, person_name, phone_num, address)
                VALUES (%s, %s, %s, %s)
            """, (person_id, name, phone, address))

            # إدخال في Customer
            cursor.execute("""
                INSERT INTO Customer (customer_id, person_id, password)
                VALUES (%s, %s, %s)
            """, (customer_id, person_id, password))

            db.commit()

            return redirect(url_for('customer'))

        except Exception as e:
            db.rollback()
            cursor.close()
            db.close()
            return str(e)

    return render_template('customer_signup.html')



if __name__ == "__main__":
    app.run(debug=True)
