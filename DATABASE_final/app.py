from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from datetime import datetime
import mysql.connector
import random
from flask import jsonify


app = Flask(__name__)
app.secret_key = "secret123"

#database connection
def get_db():
    return mysql.connector.connect(
    host="localhost",
    user="root",
    password="abeer@122S",
    database="salehkalaf"
    )

#route for the main bage 
@app.route('/')
def home():
    return render_template('test.html')



# Route to select between Employee and Manager
@app.route('/staff')
def staff():
    return render_template('staff.html')


# employee stuff
@app.route('/employee', methods=['GET', 'POST'])
def employee():
    error = None
    if request.method == 'POST':
        eid_formatted = request.form['employee_id']
        pw = request.form['password']
        
        # parse the formatted ID to get numeric ID
        try:
            eid = parse_employee_id(eid_formatted)
        except:
            error = "Invalid Employee ID format"
            return render_template('employee_login.html', error=error)

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "select * from Employee where employee_id=%s and password=%s",
            (eid, pw)
        )
        emp = cursor.fetchone()
        cursor.close()
        db.close()

        if emp:
            session['employee_id'] = eid  # Store numeric ID in session
            session['category'] = emp['category']
            session['branch_id'] = emp['branch_id']
            session['warehouse_id'] = emp['warehouse_id']

            if emp['category'] == 'branchEmployee':
                return redirect(url_for('branch_employee_dashboard'))
            elif emp['category'] == 'warehouseEmployee':
                return redirect(url_for('Warehouse_employee_Dashboard'))
            else:
                error = "Unknown Employee Category"
        else:
            error = "Invalid Employee ID or Password"

    return render_template('employee_login.html', error=error)

#route for employee_login  portal bage 
@app.route('/employee_portal')
def employee_portal():
    if 'employee_id' not in session:
        return redirect(url_for('employee'))
    return render_template('employee_login.html')

@app.route('/branch_employee_account')
def branch_employee_account():
  
    if 'employee_id' not in session or session.get('category') != 'branchEmployee':
        return redirect(url_for('employee'))

    employee_id = session['employee_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        select e.employee_id, e.person_id, e.category, e.salary, e.branch_id, e.warehouse_id,
               p.person_name, p.address,p.phone_num
        from Employee e
        join Person p on e.person_id = p.person_id
        Where e.employee_id = %s
    """, (employee_id,))
    employee = cursor.fetchone()
    employee['formatted_id'] = format_employee_id(employee['employee_id'], employee['category'])

    
    cursor.execute("select branch_name, branch_location from Branch where branch_id = %s", (employee['branch_id'],))
    branch = cursor.fetchone()

    return render_template('branch_employee_account.html', employee=employee, branch=branch)

@app.route('/branch_employee_dashboard')
def branch_employee_dashboard():
    if 'employee_id' not in session:
        return redirect(url_for('employee'))

    emp = {
    'employee_id':session['employee_id'],
    'category':session['category'],
    'branch_id':session['branch_id']
    } 
    if emp['category'] != 'branchEmployee':
        return "Access Denied", 403
    
    branch = session['branch_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        select
            e.employee_id,
            e.category,
            e.salary,
            p.person_name,
            p.phone_num,
            p.address
        from Employee e
        join Person p ON e.person_id = p.person_id
        where e.employee_id = %s
    """, (emp['employee_id'],))
    employee_info = cursor.fetchone()

    employee_info['formatted_id'] = format_employee_id(employee_info['employee_id'], employee_info['category'])

    cursor.execute("""
        select branch_id, branch_name, branch_location, branch_status, branch_capacity
        from Branch
        where branch_id = %s
    """, (emp['branch_id'],))
    branch_info = cursor.fetchone()


    cursor.execute("""
        select bp.product_id, p.product_name, bp.available_quantity, p.price, p.product_unit,p.reOrder_level
        from branch_Product bp
        join Product p on bp.product_id = p.product_id
        where bp.branch_id = %s
    """, (emp['branch_id'],))
    branch_products = cursor.fetchall()

    # Low stock products
    low_stock_products = [prod for prod in branch_products if prod['available_quantity'] <= prod['reOrder_level']]

# get employee notifications
    cursor.execute("""
        select notification_id, notification_type, message, created_date, is_read
from Notification
where employee_id = %s
  and is_read = 0
order by created_date DESC
limit 10

    """, (emp['employee_id'],))
    notifications = cursor.fetchall()

    # first 2 employees only
    cursor.execute("""
    select e.employee_id, p.person_name, e.category
    from Employee e
    join Person p on e.person_id = p.person_id
    where e.branch_id = %s
    limit 2
    """, (branch,))
    preview_employees = cursor.fetchall()
    for emp_item in preview_employees:
        emp_item['formatted_id'] = format_employee_id(emp_item['employee_id'], emp_item['category'])
    
    cursor.execute("""
    select 
        e.employee_id,
        p.person_name,
        p.phone_num,
        p.address,
        e.category,
        e.salary
    from Employee e
    join Person p on e.person_id = p.person_id
    where e.branch_id = %s
    """, (branch,))
    all_employees = cursor.fetchall()

    for emp_item in all_employees:
        emp_item['formatted_id'] = format_employee_id(emp_item['employee_id'], emp_item['category'])

    cursor.close()

    return render_template(
       "Branch_employee_Dashboard.html",
        employee=employee_info,
        branch=branch_info,
        preview_employees=preview_employees,
        all_employees=all_employees,
        branch_products=branch_products,
        low_stock_products=low_stock_products,
        notifications=notifications
    )


@app.route('/add_employee_page')
def add_employee_page():
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager'))
    return render_template("add_employee.html")


@app.route('/add_employee', methods=['POST'])
def add_employee():
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager'))
    branch_id = session['branch_id']

    # manager  id  is auto increment 
    person_id = request.form['person_id']
    name = request.form['person_name']
    phone = request.form['phone_num']
    address = request.form['address']
    salary = request.form['salary']
    password = request.form['password']

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("select * from Person where person_id=%s", (person_id,))
        if cursor.fetchone():
            cursor.execute("""
                update Person
                set person_name=%s, phone_num=%s, address=%s
                where person_id=%s
            """,(name,phone,address,person_id))
        else:
            cursor.execute("""
                insert into Person(person_id,person_name,phone_num,address)
                values(%s,%s,%s,%s)
            """,(person_id,name,phone,address))

        # Insert employee without specifying employee_id (auto-increment)
        cursor.execute("""
            insert into Employee(person_id,category,salary,branch_id,password)
            values(%s,'branchEmployee',%s,%s,%s)
        """,(person_id,salary,branch_id,password))

        db.commit()
        return redirect(url_for('branch_employees_page'))
    except Exception as e:
        db.rollback()
        return str(e)

    finally:
        cursor.close()
        db.close()

@app.route('/check_person_id', methods=['POST'])
def check_person_id():
    data = request.get_json()
    person_id = data.get('person_id')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("select * from Person where person_id=%s", (person_id,))
    person = cursor.fetchone()

    if person:
        cursor.execute("select * from Manager where person_id=%s", (person_id,))
        if cursor.fetchone():
            return jsonify({"status":"error","message":"Already a Manager "})

        cursor.execute("select * from Employee where person_id=%s", (person_id,))
        if cursor.fetchone():
            return jsonify({"status":"error","message":"Already an Employee "})

        return jsonify({"status":"ok","message":"Person exists "})
    else:
        return jsonify({"status":"ok","message":"New Person "})


@app.route('/update_employee_salary', methods=['POST'])
def update_employee_salary():
    emp_id = request.form['employee_id']
    salary = request.form['salary']

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        update Employee set salary = %s where employee_id = %s
    """, (salary, emp_id))
    db.commit()

    return redirect(url_for('branch_employees_page'))

@app.route('/delete_employees', methods=['POST'])
def delete_employees():
    data = request.get_json()
    ids = data.get('employees', [])

    if not ids:
        return '', 400

    db = get_db()
    cursor = db.cursor()

    try:
        for emp_id in ids:
  # 1.delete notifications
            cursor.execute("""
                delete from Notification
                where employee_id = %s
            """, (emp_id,))

            # 2.delete order requests
            cursor.execute("""
                delete from OrderRequest
                where employee_id = %s
            """, (emp_id,))

            # 3.get person_id
            cursor.execute("""
                select person_id from Employee
                where employee_id = %s
            """, (emp_id,))
            row = cursor.fetchone()

            if not row:
                continue

            person_id = row[0]

            # 4.  check manager 
            cursor.execute("""
                select person_id from Manager
                where person_id = %s
            """, (person_id,))
            if cursor.fetchone():
                db.rollback()
                return {
                    "error": "a person cant be employee and manager at the same time"
                }, 400

            # 5.check customer
            cursor.execute("""
                select person_id from Customer
                where person_id = %s
            """, (person_id,))
            is_customer = cursor.fetchone() is not None

            # 6.delete employee
            cursor.execute("""
                delete from Employee
                where employee_id = %s
            """, (emp_id,))

            # 7.delete person ONLY if not customer
            if not is_customer:
                cursor.execute("""
                    delete from Person
                    where person_id = %s
                """, (person_id,))

        db.commit()
        return '', 204

    except Exception as e:
        db.rollback()
        print(f"Error deleting employees: {e}")
        return str(e), 500

    finally:
        cursor.close()
        db.close()


@app.route('/employees_sorted_by_salary')
def employees_sorted_by_salary():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        select p.person_name, p.phone_num, e.salary
        from Employee e
        join Person p ON e.person_id = p.person_id
        order by e.salary DESC
    """)
    employees = cursor.fetchall()

    return render_template("employees_by_salary.html", employees=employees)

@app.route('/branch/employees')
def branch_employees_page():
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager'))

    branch_id = session['branch_id']

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        select
            e.employee_id,
            p.person_name,
            p.person_id,
            p.phone_num,
            p.address,
            e.category,
            e.salary
        from Employee e
        join Person p ON e.person_id = p.person_id
        where e.branch_id = %s
    """, (branch_id,))

    employees = cursor.fetchall()
    cursor.close()

    return render_template(
        'branch_employees.html',
        employees=employees
    )


@app.route('/warehouse_employee_dashboard')
def Warehouse_employee_Dashboard():
    if 'employee_id' not in session or session.get('category') != 'warehouseEmployee':
        return redirect(url_for('employee'))

    employee_id = session['employee_id']
    
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # get the warhouse id of the employee
    cursor.execute("select warehouse_id From Employee Where employee_id = %s", (employee_id,))
    warehouse_row = cursor.fetchone()
    if not warehouse_row or not warehouse_row['warehouse_id']:
        return "No warehouse for this employee", 400
    warehouse_id = warehouse_row['warehouse_id']

#  emp info 
    cursor.execute("""
        select 
            e.employee_id,
            e.category,
            e.salary,
            p.person_name,
            p.phone_num,
            p.address
        from Employee e
        join Person p on e.person_id = p.person_id
        where e.employee_id = %s
    """, (employee_id,))
    employee_info = cursor.fetchone()
    employee_info['formatted_id'] = format_employee_id(employee_info['employee_id'], employee_info['category'])

   
    cursor.execute("select * from Warehouse where warehouse_id = %s", (warehouse_id,))
    warehouse = cursor.fetchone()


# get products in the warehouse
    cursor.execute("""
        select wp.product_id, p.product_name, wp.available_quantity AS available_quantity , p.reOrder_level
        from warehouse_Product wp
        join Product p on wp.product_id = p.product_id
        where wp.warehouse_id = %s
    """, (warehouse_id,))
    warehouse_products = cursor.fetchall()

    #  checkk low stock products in the warehouse 
    low_stock_products = [prod for prod in warehouse_products if prod['available_quantity'] <= prod['reOrder_level']]


    # Pending stocking requests
    cursor.execute("""
        select r.request_id, r.product_id, p.product_name, r.request_quantity, r.req_status,
               r.branch_id, b.branch_name, r.request_date, r.notes
        from OrderRequest r
        join Product p on p.product_id = r.product_id
        join Branch b on b.branch_id = r.branch_id
        where r.warehouse_id = %s and r.req_status = 'PENDING_WAREHOUSE_EMPLOYEE'
        order by r.request_date DESC
    """, (warehouse_id,))
    pending_transfers = cursor.fetchall()

    # Notifications
    cursor.execute("""
        select notification_id, notification_type, message, created_date, is_read
from Notification
where employee_id = %s
  and is_read = 0
order by created_date DESC
limit 10

    """, (employee_id,))

    notifications = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
     'Wearhouse_employee_Dashboard.html',
        employee=employee_info,
        warehouse=warehouse,
        warehouse_products=warehouse_products,
        low_stock_products=low_stock_products,
        pending_transfers=pending_transfers,
        notifications=notifications
    )

@app.route('/warehouse_employee_account')
def warehouse_employee_account():
    if 'employee_id' not in session:
        return redirect(url_for('employee'))

    employee_id = session['employee_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # get employee info and his person details
    cursor.execute("""
        select e.employee_id, e.person_id, e.category, e.salary, e.branch_id, e.warehouse_id,
               p.person_name, p.address, p.phone_num
        from Employee e
        join Person p on e.person_id = p.person_id
        where e.employee_id = %s
    """, (employee_id,))
    employee = cursor.fetchone()
    employee['formatted_id'] = format_employee_id(employee['employee_id'], employee['category'])

    branch = None
    warehouse = None

# branch info if exist
    if employee.get('branch_id'):
        cursor.execute("select branch_name, branch_location from Branch where branch_id = %s", (employee['branch_id'],))
        branch = cursor.fetchone()

#warhouse info if exist
    if employee.get('warehouse_id'):
        cursor.execute("select p.* from Product p join warehouse_product wp on p.product_id = wp.product_id where wp.warehouse_id = %s", (employee['warehouse_id'],))
        warehouse = cursor.fetchone()

    return render_template(
        'warehouse_employee_account.html',
        employee=employee,
        branch=branch,
        warehouse=warehouse
    )


# manager stuff


@app.route('/manager', methods=['GET', 'POST'])
def manager():
    error = None
    if request.method == 'POST':
        mid_formatted = request.form['manager_id']
        pw = request.form['password']
        
        # parse the  ID to get the orgin num 
        try:
            mid = parse_manager_id(mid_formatted)
        except:
            error = "invalid manager ID format"
            return render_template('manager_login.html', error=error)

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "select * from Manager where manager_id=%s and password=%s",
            (mid, pw)
        )
        mgr = cursor.fetchone()
        cursor.close()
        db.close()

        if mgr:
            session['manager_id'] = mid  # store number of ID
            session['category'] = mgr['category']
            session['branch_id'] = mgr['branch_id']
            session['warehouse_id'] = mgr['warehouse_id']

            if mgr['category'] == 'branchManager':
                return redirect(url_for('branch_manager_dashboard'))
            elif mgr['category'] == 'warehouseManager':
                return redirect(url_for('warehouse_manager_dashboard'))
            else:
                error = "Unknown Manager Category"
        else:
            error = "Invalid Manager ID or Password"

    return render_template('manager_login.html', error=error)

@app.route('/branch_contacts')
def branch_contacts():
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
                   
       select b.branch_id,
            b.branch_name,
            b.branch_location,
            p.person_name AS manager_name
        from Branch b
        left join Manager m
            on m.branch_id = b.branch_id
           and m.category = 'branchManager'
        left join Person p
            on m.person_id = p.person_id
    """)

    branches = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('branch_contacts.html', branches=branches)

@app.route('/branch_reports')
def branch_reports():
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # get branches id to put in combobox
    cursor.execute("select branch_id, branch_name FROM Branch")
    all_branches = cursor.fetchall()

    selected_branch = request.args.get('branch_id', 'all')
    period = request.args.get('period', 'monthly')

    cursor.execute("""
        select b.branch_id, b.branch_name, b.branch_location,
               count(e.employee_id) as employee_count
        from Branch b
        left join Employee e on b.branch_id = e.branch_id
        group by b.branch_id, b.branch_name, b.branch_location
    """)
    employees_count = cursor.fetchall()

    cursor.execute("""
        select b.branch_id, b.branch_name, b.branch_location,
               IFNULL(sum(i.total_amount),0) as total_sales
        from Branch b
        left join Sales_Invoice i ON b.branch_id = i.branch_id
        group by b.branch_id, b.branch_name, b.branch_location
    """)
    sales_per_branch = cursor.fetchall()

    city = "Ramallah"
    cursor.execute("""
        select b.branch_id, b.branch_name, b.branch_location,
               count(i.invoice_id) as total_invoices,
               IFNULL(SUM(i.total_amount),0) as total_sales
        from Branch b
       left join Sales_Invoice i on b.branch_id = i.branch_id
        where b.branch_location = %s
        group by b.branch_id, b.branch_name, b.branch_location
    """, (city,))
    branches_city = cursor.fetchall()

    cursor.execute("""
        select b.branch_id, b.branch_name, b.branch_location,
               count(DISTINCT i.customer_id) as total_customers,
               IFNULL(sum(i.total_amount),0) as total_purchases
        from Branch b
       left join Sales_Invoice i on b.branch_id = i.branch_id
        group by b.branch_id, b.branch_name, b.branch_location
        order by total_customers DESC, total_purchases DESC
        limit 1
    """)
    top_branch = cursor.fetchone()

    branch_filter = ""
    params = []
    if selected_branch != "all":
        branch_filter = " and si.branch_id = %s"
        params.append(selected_branch)

    date_filter = ""
    if period == "daily":
        date_filter = " and DATE(si.invoice_date) = CURDATE()"
    elif period == "monthly":
        date_filter = " and MONTH(si.invoice_date) = MONTH(CURDATE()) and YEAR(si.invoice_date) = YEAR(CURDATE())"
    elif period == "yearly":
        date_filter = " and YEAR(si.invoice_date) = YEAR(CURDATE())"

    # Best Product
    cursor.execute(f"""
        select p.product_id, p.product_name, sum(ip.quantity) as total_sold
        from Sales_Invoice si
        join invoice_product ip on si.invoice_id = ip.invoice_id
        join Product p on p.product_id = ip.product_id
        where 1=1 {branch_filter} {date_filter}
        group by p.product_id, p.product_name
        order by total_sold DESC
        limit 1
    """, tuple(params))
    best_product = cursor.fetchone()

    # worst Product
    cursor.execute(f"""
        select p.product_id, p.product_name, sum(ip.quantity) AS total_sold
        from Sales_Invoice si
        join invoice_product ip on si.invoice_id = ip.invoice_id
        join Product p on p.product_id = ip.product_id
        where 1=1 {branch_filter} {date_filter}
        group by p.product_id, p.product_name
        order by total_sold ASC
        limit 1
    """, tuple(params))
    worst_product = cursor.fetchone()

    # total sales for a certain branch in a certaib period of time
    period_sales_query = "select IFNULL(sum(total_amount),0) as period_sales from Sales_Invoice where 1=1"
    period_params = []

    if selected_branch != "all":
        period_sales_query += " and branch_id = %s"
        period_params.append(selected_branch)

    if period == "daily":
        period_sales_query += " and DATE(invoice_date) = CURDATE()"
    elif period == "monthly":
        period_sales_query += " and MONTH(invoice_date) = MONTH(CURDATE()) and YEAR(invoice_date) = YEAR(CURDATE())"
    elif period == "yearly":
        period_sales_query += " and YEAR(invoice_date) = YEAR(CURDATE())"

    cursor.execute(period_sales_query, tuple(period_params))
    period_sales = cursor.fetchone()['period_sales']

    # num of products based on the supplier 
    branch_for_category = request.args.get('branch_category', 'all')
    branch_filter_category = ""
    params_category = []

    if branch_for_category != "all":
        branch_filter_category = " and bp.branch_id = %s"
        params_category.append(branch_for_category)

    cursor.execute(f"""
        select p.product_category AS category_name, sp.supplier_name, COUNT(p.product_id) AS total_products
        from Product p
        
        join supplier_product s ON s.product_id = p.product_id
        join branch_Product bp ON p.product_id = bp.product_id
        join Supplier sp on sp.supplier_id = s.supplier_id
        where 1=1 {branch_filter_category}
        group by p.product_category, sp.supplier_name
        order by sp.supplier_name ASC;
    """, tuple(params_category))
    products_per_category = cursor.fetchall()

    cursor.execute("select branch_id, branch_name from Branch")
    all_branches_category = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('branch_reports.html',
                           employees_count=employees_count,
                           sales_per_branch=sales_per_branch,
                           branches_city=branches_city,
                           top_branch=top_branch,
                           city=city,
                           all_branches=all_branches,
                           selected_branch=selected_branch,
                           period=period,
                           best_product=best_product,
                           worst_product=worst_product,
                           period_sales=period_sales,
                           products_per_category=products_per_category,
                           all_branches_category=all_branches_category,
                           branch_for_category=branch_for_category)


@app.route('/branch_manager_dashboard')
def branch_manager_dashboard():
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager_login'))

    manager_id = session['manager_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # branch info 
    cursor.execute("""
        select b.branch_id, b.branch_name, b.branch_location
        from Branch b
        join Manager m on m.branch_id = b.branch_id
        where m.manager_id = %s
    """, (manager_id,))
    branch = cursor.fetchone()

     # get branch products 
    cursor.execute("""
        select p.product_id, p.product_name, wq.available_quantity as available_quantity, p.reOrder_level
        from  branch_product wq
        join Product p on p.product_id = wq.product_id
        where wq.branch_id = %s
    """, (branch['branch_id'],))
    branch_products = cursor.fetchall()

 # pending requests , need to deal with
    cursor.execute("""
        select r.request_id, r.product_id, p.product_name, r.request_quantity, r.req_status, r.request_date,
               e.employee_id, pe.person_name as employee_name,
               wp.available_quantity as warehouse_qty
        from OrderRequest r
        join Product p on p.product_id = r.product_id
        join Employee e on e.employee_id = r.employee_id
        join Person pe on pe.person_id = e.person_id
        left join warehouse_Product wp on wp.warehouse_id = r.warehouse_id and wp.product_id = r.product_id
        where r.branch_id = %s and r.req_status = 'PENDING_BRANCH_MANAGER'
        order by r.request_date DESC
    """, (branch['branch_id'],))
    pending_requests = cursor.fetchall()

    for req in pending_requests:
        req['formatted_employee_id'] = format_employee_id(req['employee_id'], 'branchEmployee')  

# get all requests for tracking
    cursor.execute("""
        select r.request_id, r.product_id, p.product_name, r.request_quantity, r.req_status, r.request_date,
               r.branch_manager_response_date, r.warehouse_response_date, r.notes
        from OrderRequest r
        join Product p on p.product_id = r.product_id
        where r.branch_id = %s
        order by r.request_date DESC
        limit 20
    """, (branch['branch_id'],))
    all_requests = cursor.fetchall()

    # num of employees 
    cursor.execute("""
    select count(*) as total
    from Employee
    where branch_id = %s
    """, (branch['branch_id'],))

    total_employees = cursor.fetchone()['total']


# get branch employees
    cursor.execute("""
        select e.employee_id, e.category, e.salary,
               p.person_name, p.phone_num
        from Employee e
        join Person p on e.person_id = p.person_id
        where e.branch_id = %s
    """, (branch['branch_id'],))
    branch_employees = cursor.fetchall()
    for emp in branch_employees:
        emp['formatted_id'] = format_employee_id(emp['employee_id'], emp['category'])

    # notifications
    cursor.execute("""
        select notification_id, notification_type, message, created_date, is_read
        from Notification
        where manager_id = %s
        and is_read = 0
        order by created_date DESC
        limit 10

    """, (manager_id,))
    notifications = cursor.fetchall()

    cursor.close()
    db.close()


    return render_template(
        'branch_manager_dashboard.html',
        branch=branch,
        branch_products=branch_products,
        pending_requests=pending_requests,
        all_requests=all_requests,
        total_employees=total_employees,
        branch_employees=branch_employees,
        notifications=notifications
    )


@app.route('/branch/<int:branch_id>/employees')
def lest_branch_employees(branch_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
    select 
        e.employee_id,
        p.person_name as employee_name,
        p.phone_num as employee_phone,
        p.address as employee_address,
        e.category as employee_category,
        e.salary as employee_salary,
        m.manager_id,
        mp.person_name as manager_name,
        mp.phone_num as manager_phone
    from Employee e
    join Person p on e.person_id = p.person_id
    left join Manager m on m.branch_id = e.branch_id and m.category = 'branchManager'
    left join Person mp on m.person_id = mp.person_id
    where e.branch_id = %s;
    """

    cursor.execute(query, (branch_id,))
    employees = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('lest_branch_employees.html', employees=employees)


@app.route('/branch_manager_account')
def branch_manager_account():
    # log in as manager
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager')) 

    manager_id = session['manager_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # get manager info 
    cursor.execute("""
        select m.manager_id as employee_id, m.person_id, m.category, m.salary, m.branch_id,
               p.person_name, p.address, p.phone_num
        from Manager m
        join Person p on m.person_id = p.person_id
        where m.manager_id = %s
    """, (manager_id,))
    manager = cursor.fetchone()
    manager['formatted_id'] = format_manager_id(manager['employee_id'], manager['category'])

    if not manager:
        return "Manager not found", 404

    branch_id = manager['branch_id']

# get branch info 
    cursor.execute("select branch_name, branch_location from Branch where branch_id = %s", (branch_id,))
    branch = cursor.fetchone()

   # get branch employeeas 
    cursor.execute("""
        select e.employee_id, e.category, e.salary,
               p.person_name, p.phone_num
        from Employee e
        join Person p on e.person_id = p.person_id
        where e.branch_id = %s
    """, (branch_id,))
    branch_employees = cursor.fetchall()
    for emp in branch_employees:
        emp['formatted_id'] = format_employee_id(emp['employee_id'], emp['category'])


    notifications = ["the meeting is at 10 AM", "here is the weekly report"]

    return render_template(
        'branch_manager_account.html',
        employee=manager,          
        branch=branch,
        branch_employees=branch_employees,
        notifications=notifications
    )

@app.route('/warehouse_manager_dashboard')
def warehouse_manager_dashboard():
    if 'manager_id' not in session or session.get('category') != 'warehouseManager':
        return redirect(url_for('manager_login'))

    manager_id = session['manager_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

     # get warehouse data
    cursor.execute("""
        select w.warehouse_id, w.warehouse_location
        from Warehouse w
        join Manager m on m.warehouse_id = w.warehouse_id
        where m.manager_id = %s
    """, (manager_id,))
    warehouse = cursor.fetchone()

# get warehouse capacity & filling
    cursor.execute("""
    select 
        w.warehouse_capacity,
        sum(wp.available_quantity) as current_filling
    from Warehouse w
    left join warehouse_product wp 
        on wp.warehouse_id = w.warehouse_id
    where w.warehouse_id = %s
    group by w.warehouse_capacity
    """, (warehouse['warehouse_id'],))

    warehouse_status = cursor.fetchone()

    warehouse_capacity = warehouse_status['warehouse_capacity']
    current_filling = warehouse_status['current_filling']

    status = (
    "FULL" if current_filling >= warehouse_capacity
    else "NEAR FULL" if current_filling >= warehouse_capacity * 0.9
    else "AVAILABLE"
    )

    # get warehouse products
    cursor.execute("""
        select p.product_id, p.product_name, wq.available_quantity AS available_quantity, p.reOrder_level
        from warehouse_product wq
        join Product p on p.product_id = wq.product_id
        where wq.warehouse_id = %s
    """, (warehouse['warehouse_id'],))
    warehouse_products = cursor.fetchall()

    # requests needing actions
    cursor.execute("""
        select r.request_id, r.branch_id, b.branch_name, r.product_id, p.product_name, 
               r.request_quantity, r.req_status, r.request_date, r.notes,
               wp.available_quantity as warehouse_qty
        from OrderRequest r
        join Branch b on b.branch_id = r.branch_id
        join Product p on p.product_id = r.product_id
        left join warehouse_Product wp on wp.warehouse_id = r.warehouse_id and wp.product_id = r.product_id
        where r.warehouse_id = %s and r.req_status = 'PENDING_WAREHOUSE_MANAGER'
        order by r.request_date DESC
    """, (warehouse['warehouse_id'],))
    pending_purchase_requests = cursor.fetchall()

    # get suppliers
    cursor.execute("select supplier_id, supplier_name from supplier")
    suppliers = cursor.fetchall()

    # count warehouse employees
    cursor.execute("""
        select count(*) as total
        from Employee
        where warehouse_id = %s
    """, (warehouse['warehouse_id'],))
    total_employees = cursor.fetchone()['total']

    # get warehouse employees (show first 2 and then follow by the link )
    # I edited it it doesnt show 2 any more you directly go to anew html page and see all 
    cursor.execute("""
        select e.employee_id, e.category, e.salary,
               p.person_name, p.phone_num
        from Employee e
        join Person p on e.person_id = p.person_id
        where e.warehouse_id = %s
        limit 2
    """, (warehouse['warehouse_id'],))
    warehouse_employees = cursor.fetchall()
    for emp in warehouse_employees:
        emp['formatted_id'] = format_employee_id(emp['employee_id'], emp['category'])

    # notifications
    cursor.execute("""
       select notification_id, notification_type, message, created_date, is_read
       from Notification
       where manager_id = %s
       and is_read = 0
       order by created_date DESC
       limit 10

    """, (manager_id,))
    notifications = cursor.fetchall()
     #  supplier who provides the most products
    cursor.execute("""
        select s.supplier_id, s.supplier_name, count(p.product_id) as total_products
        from Supplier s
        join supplier_product p ON p.supplier_id = s.supplier_id
        group by s.supplier_id
        order by total_products DESC
        limit 1
    """)
    top_supplier = cursor.fetchone()


    #  tot products per supplier with product names
    cursor.execute("""
        select s.supplier_id, s.supplier_name, pt.product_name
        from Supplier s
        join supplier_product p on p.supplier_id = s.supplier_id
        join Product pt on pt.product_id = p.product_id
        order by s.supplier_id
    """)
    rows = cursor.fetchall()

    temp = {}
    for row in rows:
        sid = row['supplier_id']
        if sid not in temp:
            temp[sid] = {
                'supplier_name': row['supplier_name'],
                'products': []
            }
        temp[sid]['products'].append(row['product_name'])

    suppliers_products = []
    for sid, data in temp.items():
        suppliers_products.append({
            'supplier_id': sid,
            'supplier_name': data['supplier_name'],
            'total_products': len(data['products']),
            'product_names': ', '.join(data['products'])
        })
    #  tot quantity supplied to each warehouse by each supplier
    cursor.execute("""
        select s.supplier_id, s.supplier_name, w.warehouse_id, w.warehouse_location,
               sum(wp.available_quantity) as total_quantity_supplied
        from Supplier s
        join supplier_product p on p.supplier_id = s.supplier_id
        join Warehouse_Product wp on wp.product_id = p.product_id
        join Warehouse w on w.warehouse_id = wp.warehouse_id
        group by s.supplier_id, w.warehouse_id
    """)
    supplier_to_warehouse = cursor.fetchall()


    cursor.close()
    db.close()

    return render_template(
        'Wearhouse_Manager_Dashboard.html',
        warehouse_id=warehouse['warehouse_id'],
        warehouse_location=warehouse['warehouse_location'],
        warehouse_products=warehouse_products,
        total_employees=total_employees,
        warehouse_employees=warehouse_employees,
        pending_purchase_requests=pending_purchase_requests,
        suppliers=suppliers,
        warehouse_capacity = warehouse_capacity,
        current_filling=current_filling,
        warehouse_status=status,
        notifications=notifications,
        top_supplier=top_supplier,
        suppliers_products=suppliers_products,
        supplier_to_warehouse=supplier_to_warehouse
    )


@app.route('/warehouse_contacts')
def warehouse_contacts():
    if 'manager_id' not in session or session.get('category') != 'warehouseManager':
        return redirect(url_for('manager'))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
                   
       select w.warehouse_id,
            w.branch_id,
            w.warehouse_location,
            w.warehouse_PhoneNum,
            p.phone_num,
            p.person_name AS manager_name,
            b.branch_name
        from Warehouse w
        left join Manager m
            on m.warehouse_id = w.warehouse_id
           and m.category = 'warehouseManager'
        left join Person p
            on m.person_id = p.person_id
        join Branch b on w.branch_id = b.branch_id
    """)

    warehouses = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('warehouse_contacts.html', warehouses=warehouses)

@app.route('/warehouse/employees')
def warehouse_employees_page():
    if 'manager_id' not in session or session.get('category') != 'warehouseManager':
        return redirect(url_for('manager'))

    warehouse_id = session['warehouse_id']

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        select
            e.employee_id,
            e.person_id,
            p.person_name,
            p.phone_num,
            p.address,
            e.category,
            e.salary
        from Employee e
        join Person p on e.person_id = p.person_id
        where e.warehouse_id = %s
    """, (warehouse_id,))

    employees = cursor.fetchall()
    for emp in employees:
        emp['formatted_id'] = format_employee_id(emp['employee_id'], emp['category'])
    
    cursor.close()

    return render_template(
        'warehouse_employees.html',
        employees=employees
    )

@app.route('/warehouse_purchase_orders')
def warehouse_purchase_orders():
    if 'manager_id' not in session or session.get('category') != 'warehouseManager':
        return redirect(url_for('manager_login'))

    manager_id = session['manager_id']

    period=request.args.get('period','day')
    date=request.args.get('date')
    year=request.args.get('year')
    month=request.args.get('month')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    #  get warehouse id by manager
    cursor.execute("""
        select w.warehouse_id
        from Warehouse w
        join manager m on  m.warehouse_id = w.warehouse_id
        where m.manager_id = %s
    """, (manager_id,))

    manager_warehouse = cursor.fetchone()

    if not manager_warehouse:
        cursor.close()
        db.close()
        return "Warehouse not assigned to this manager", 403

    warehouse_id = manager_warehouse['warehouse_id']


    # all suppliers
    cursor.execute("""
    select supplier_id, supplier_name, phone_num, email
    from Supplier
    """)
    all_suppliers = cursor.fetchall()

# suppliers that were used before (even once)
    cursor.execute("""
    select distinct supplier_id
    from Purchase_Order
    where warehouse_id = %s
    """, (warehouse_id,))
    used_suppliers = {row['supplier_id'] for row in cursor.fetchall()}


   # warehouse purchase order
    query = """
        select 
            po.order_id ,
            po.order_date,
            po.order_cost AS total_cost,
            s.supplier_name,
            s.phone_num AS phone,
            s.email
        from Purchase_Order po
        join Supplier s on s.supplier_id = po.supplier_id
        where po.warehouse_id = %s
    """
    params = [warehouse_id]

    #  date filters
    if period == 'day':
        query += """
            and po.order_date >= CURDATE()
            and po.order_date < CURDATE() + INTERVAL 1 DAY
        """

    elif period == 'month':
        query += """
            and po.order_date >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
            and po.order_date < DATE_FORMAT(CURDATE(), '%Y-%m-01') + INTERVAL 1 MONTH
        """
# gets the last 3 years results 
    elif period == 'year':
        query += """
            and po.order_date >= CURDATE() - INTERVAL 3 YEAR
        """

    query += " ORDER BY po.order_date DESC"

    cursor.execute(query, params)
    orders = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
         'warehouse_purchase_orders.html',
    orders=orders,
    selected_period=period,
    suppliers=all_suppliers,
    used_suppliers=used_suppliers
    )

@app.route('/warehouse_purchase_orders_emp')
def warehouse_purchase_orders_emp():
    if 'employee_id' not in session or session.get('category') != 'warehouseEmployee':
        return redirect(url_for('employee_login'))

    employee_id = session['employee_id']

    period = request.args.get('period', 'day')
    date = request.args.get('date')
    year = request.args.get('year')
    month = request.args.get('month')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # get warhiuse id by employee
    cursor.execute("""
        select warehouse_id
        from Employee
        where employee_id = %s
    """, (employee_id,))

    emp_warehouse = cursor.fetchone()

    if not emp_warehouse:
        cursor.close()
        db.close()
        return "Warehouse not connected to this employee", 403

    warehouse_id = emp_warehouse['warehouse_id']
    
    # all suppliers
    cursor.execute("""
    select supplier_id, supplier_name, phone_num, email
    from Supplier
    """)
    all_suppliers = cursor.fetchall()

# suppliers that were used before (even once)
    cursor.execute("""
    select  distinct supplier_id
    from Purchase_Order
    where warehouse_id = %s
    """, (warehouse_id,))
    used_suppliers = {row['supplier_id'] for row in cursor.fetchall()}

    # get purc-ords
    query = """
        select 
            po.order_id,
            po.order_date,
            po.order_cost AS total_cost,
            s.supplier_name,
            s.phone_num AS phone,
            s.email
        from Purchase_Order po
        join Supplier s on s.supplier_id = po.supplier_id
        where po.warehouse_id = %s
    """
    params = [warehouse_id]

    #  date filters
    if period == 'day':
        query += """
            and po.order_date >= CURDATE()
            and po.order_date < CURDATE() + INTERVAL 1 DAY
        """

    elif period == 'month':
        query += """
            and po.order_date >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
            and po.order_date < DATE_FORMAT(CURDATE(), '%Y-%m-01') + INTERVAL 1 MONTH
        """

    elif period == 'year':
        query += """
            and po.order_date >= CURDATE() - INTERVAL 3 YEAR
        """

    query += " ORDER BY po.order_date DESC"

    cursor.execute(query, params)
    orders = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
       'warehouse_purchase_orders_emp.html',
    orders=orders,
    selected_period=period,
    suppliers=all_suppliers,
    used_suppliers=used_suppliers
    )


@app.route('/add_warehouse_employee_page')
def add_warehouse_employee_page():
    if 'manager_id' not in session or session.get('category') != 'warehouseManager':
        return redirect(url_for('manager'))

    return render_template("add_warehouse_employee.html")


@app.route('/add_warehouse_employee', methods=['POST'])
def add_warehouse_employee():
    if 'manager_id' not in session or session.get('category') != 'warehouseManager':
        return redirect(url_for('manager'))

    warehouse_id = session['warehouse_id']
    employee_id  = request.form['employee_id']
    person_id = request.form['person_id']
    name  = request.form['person_name']
    phone   = request.form['phone_num']
    address = request.form['address']
    salary   = request.form['salary']
    password = request.form['password']

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("select * from Person where person_id=%s", (person_id,))
        if cursor.fetchone():
            cursor.execute("""
                update Person
                set person_name=%s, phone_num=%s, address=%s
                where person_id=%s
            """,(name,phone,address,person_id))
        else:
            cursor.execute("""
                insert into Person(person_id,person_name,phone_num,address)
                values(%s,%s,%s,%s)
            """,(person_id,name,phone,address))

        cursor.execute("""
            insert into Employee(employee_id,person_id,category,salary,warehouse_id,password)
            values(%s,%s,'warehouseEmployee',%s,%s,%s)
        """,(employee_id,person_id,salary,warehouse_id,password))

        db.commit()
        return redirect(url_for('warehouse_employees_page'))

    except Exception as e:
        db.rollback()
        return str(e)

    finally:
        cursor.close()
        db.close()


@app.route('/update_warehouse_employee_salary', methods=['POST'])
def update_warehouse_employee_salary():
    emp_id = request.form['employee_id']
    salary = request.form['salary']

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        update Employee set salary = %s where employee_id = %s
    """, (salary, emp_id))
    db.commit()

    return redirect(url_for('warehouse_employees_page'))


@app.route('/delete_warehouse_employees', methods=['POST'])
def delete_warehouse_employees():
    data = request.get_json()
    ids = data.get('employees', [])

    if not ids:
        return '', 400

    db = get_db()
    cursor = db.cursor()

    try:
        for emp_id in ids:
            #del notifi

            cursor.execute("""
                delete from Notification
                where employee_id = %s
            """, (emp_id,))

            #del order requests
            cursor.execute("""
                delete from OrderRequest
                where employee_id = %s
            """, (emp_id,))

#get person_id
            cursor.execute("""
                select person_id from Employee where employee_id = %s
            """, (emp_id,))
            row = cursor.fetchone()

            if row:
                person_id = row[0]

                #delete employee
                cursor.execute("""
                    delete from Employee where employee_id = %s
                """, (emp_id,))

#check if person is used elsewhere
                cursor.execute("""
                    select count(*) from Customer where person_id = %s
                """, (person_id,))
                customer_count = cursor.fetchone()[0]

                cursor.execute("""
                    select count(*) from Manager where person_id = %s
                """, (person_id,))
                manager_count = cursor.fetchone()[0]

                # only delete person if not used elsewhere
                if customer_count == 0 and manager_count == 0:
                    cursor.execute("""
                        delete from Person where person_id = %s
                    """, (person_id,))

        db.commit()
        cursor.close()
        db.close()
        return '', 204

    except Exception as e:
        db.rollback()
        cursor.close()
        db.close()
        print(f"Error deleting employees: {e}")
        return str(e), 500

@app.route('/warehouse_employees_sorted_by_salary')
def warehouse_employees_sorted_by_salary():
    if 'manager_id' not in session or session.get('category') != 'warehouseManager':
        return redirect(url_for('manager'))
    
    warehouse_id = session['warehouse_id']
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        select p.person_name, p.phone_num, e.salary
        from Employee e
        join Person p on e.person_id = p.person_id
        where e.warehouse_id = %s
        order by e.salary DESC
    """, (warehouse_id,))
    employees = cursor.fetchall()

    return render_template("warehouse_employees_by_salary.html", employees=employees)


@app.route('/warehouse_manager_account')
def warehouse_manager_account():
    # check if warehouse manager true
    if 'manager_id' not in session or session.get('category') != 'warehouseManager':
        return redirect(url_for('manager'))  

    manager_id = session['manager_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # get manager info
    cursor.execute("""
        select m.manager_id, m.category, m.salary, m.warehouse_id,
               p.person_name, p.address, p.phone_num
        from Manager m
        join Person p on m.person_id = p.person_id
        where m.manager_id = %s
    """, (manager_id,))
    manager = cursor.fetchone()
    manager['formatted_id'] = format_manager_id(manager['manager_id'], manager['category'])
    if not manager:
        return "Manager not found", 404

    warehouse_id = manager['warehouse_id']

    # get wh info 
    cursor.execute("""
        select warehouse_id, warehouse_location, warehouse_capacity
        from Warehouse
        where warehouse_id = %s
    """, (warehouse_id,))
    warehouse = cursor.fetchone()

# get warehouse product
    cursor.execute("""
        select p.product_id, p.product_name, p.product_category, p.price, p.available_quantity
        from Product p
        join warehouse_product wp on p.product_id = wp.product_id
        where wp.warehouse_id = %s
    """, (warehouse_id,))
    warehouse_products = cursor.fetchall()

    # just example, i will deal with it latter
    notifications = ["Stock check required", "New shipment arrived"]  

    cursor.close()
    db.close()

    return render_template(
        'warehouse_manager_account.html',
        manager=manager,
        warehouse=warehouse,
        warehouse_products=warehouse_products,
        notifications=notifications
    )

#route for manager_login  portal bage 
@app.route('/manager_portal')
def manager_portal():
    if 'manager_id' not in session:
        return redirect(url_for('manager'))
    return render_template('manager_login.html')

@app.route('/employee_logout')
def employee_logout():
    session.clear()
    return redirect(url_for('employee'))

@app.route('/manager_logout')
def manager_logout():
    session.clear()
    return redirect(url_for('manager'))


# CUSTOMER LOGIN
@app.route('/customer', methods=['GET', 'POST'])
def customer():
    error = None
    if request.method == 'POST':
        cid_formatted = request.form['customer_id']
        pw = request.form['password']
        
        # Parse the formatted ID
        try:
            cid = parse_customer_id(cid_formatted)
        except:
            error = "Invalid Customer ID format"
            return render_template('customer.html', error=error)
            
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "select customer_id from Customer where customer_id=%s and password=%s",
            (cid, pw)
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session['customer_id'] = cid  # Store numeric ID
            return redirect(url_for('customer_portal'))
        else:
            error = "Invalid Customer ID or Password"
    return render_template('customer.html', error=error)

@app.route('/customer_account')
def customer_account():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    #select customer data
    cursor.execute("""
        select p.person_name as customer_name, c.customer_id,
               p.phone_num as phone, p.address
        from Customer c
        join Person p on c.person_id = p.person_id
        where c.customer_id = %s
    """, (customer_id,))
    customer = cursor.fetchone()
    formatted_customer_id = format_customer_id(customer['customer_id'])

    if not customer:
        cursor.close()
        db.close()
        return redirect(url_for('customer'))

    #select the customer invoices with branch data
    cursor.execute("""
        select si.invoice_id, si.invoice_date, si.total_amount,
               si.payment_method, b.branch_name, b.branch_location
        from sales_invoice si
        join branch b on si.branch_id = b.branch_id
        where si.customer_id = %s
        order by si.invoice_date DESC
    """, (customer_id,))
    invoices = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        'customer_account.html',
        customer_name=customer['customer_name'],
        customer_id=formatted_customer_id,
        phone=customer['phone'],
        address=customer['address'],
        invoices=invoices
    )


# CUSTOMER sign up 
@app.route('/customer_signup', methods=['GET', 'POST'])
def customer_signup():
    if request.method=='POST':
        name=request.form['name']
        phone= request.form['phone']
        address= request.form['address']
        password= request.form['password']
        
        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # Get new person_id
            cursor.execute("select IFNULL(max(person_id), 0) + 1 as new_id from Person")
            person_id = cursor.fetchone()['new_id']

            # insert person
            cursor.execute("""
                insert into Person (person_id, person_name, phone_num, address)
                values (%s, %s, %s, %s)
            """, (person_id, name, phone, address))

            # insert customer (ID will auto-increment)
            cursor.execute("""
                insert into Customer (person_id, password)
                values (%s, %s)
            """, (person_id, password))
            
            # get the autogenerated customer_id
            customer_id = cursor.lastrowid

            db.commit()
            cursor.close()
            db.close()

            formatted_id = format_customer_id(customer_id)
            return render_template('customer_signup.html', 
                                 success=f"Account created! Your Customer ID is: {formatted_id}")

        except mysql.connector.errors.IntegrityError as e:
            db.rollback()
            cursor.close()
            db.close()
            error = "Error creating account. Please try again."
            return render_template('customer_signup.html', error=error)

    return render_template('customer_signup.html')

# CUSTOMER LOGOUT
@app.route('/customer_logout')
def customer_logout():
    session.clear()
    return redirect(url_for('customer'))

@app.route('/customer_portal')
def customer_portal():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))
    return render_template('customer_login.html')


@app.route('/customer_products', methods=['GET'])
def customer_products():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']
    selected_branch = session.get('selected_branch')
    new_branch = request.args.get('branch_id')
    if new_branch:
        session['selected_branch']= new_branch
        selected_branch = new_branch

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # branches
    cursor.execute("""
        select branch_id, branch_name, branch_location
        from branch
        where branch_status in ('ACTIVE','OPEN')
    """)
    branches = cursor.fetchall()

    products_by_category = {}

    # products (after Confirm)
    if selected_branch:
        session['selected_branch'] = selected_branch   
        cursor.execute("""
            select
                p.product_id,
                p.product_name,
                p.product_category,
                p.price,
                bp.available_quantity as available_quantity,
                p.product_unit,
                p.product_discretion
                from branch_Product bp
                join Product p on bp.product_id = p.product_id
                where bp.branch_id = %s
                 and bp.available_quantity > 0
                 and p.product_status = 'available'
        """, (selected_branch,))


        products = cursor.fetchall()

        for p in products:
            category = p['product_category']
            products_by_category.setdefault(category, []).append(p)

    
    # show cart
    cursor.execute("""
        select p.product_name, cp.quantity, p.price,
               (cp.quantity * p.price) AS total
        from Cart c
        join cart_product cp on c.cart_id = cp.cart_id
        join Product p on cp.product_id = p.product_id
        where c.customer_id = %s
    """, (customer_id,))
    cart_preview = cursor.fetchall()

    cart_total = sum(item['total'] for item in cart_preview)

    cursor.close()
    db.close()

    category_images = {
        "فواكه مجففة | Dried Fruits": url_for('static', filename='4.jpg'),
        "بهارات | Spices": url_for('static', filename='S1.jpg'),
        "زيوت | Oils": url_for('static', filename='3.jpg'),
    }

    category_descriptions = {
        "فواكه مجففة | Dried Fruits": "أفضل الفواكه المجففة الطازجة والمغذية.",
        "بهارات | Spices": "بهارات متنوعة لتجهيز أشهى الأكلات.",
        "زيوت | Oils": "زيوت طبيعية وعالية الجودة للطهي.",
    }

    return render_template(
        'customer_products.html',
        branches=branches,
        selected_branch=selected_branch,
        products_by_category=products_by_category,
        category_images=category_images,
        category_descriptions=category_descriptions,
        cart_preview=cart_preview,
        cart_total=cart_total
    )

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']
    product_id = request.form['product_id']

    try:
        quantity = int(request.form['quantity'])
        if quantity <= 0:
            return redirect(url_for(
                'customer_products',
                error_product=product_id,
                error_msg="Quantity must be greater than zero"
            ))
        
    except ValueError:
        return redirect(url_for(
            'customer_products',
            error_product=product_id,
            error_msg="Quantity must be a number"
        ))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    branch_id = session.get('selected_branch')

    cursor.execute("""
    SELECT available_quantity
    FROM branch_Product
    WHERE product_id = %s AND branch_id = %s
""", (product_id, branch_id))

    product = cursor.fetchone()

    if not product:
        cursor.close()
        db.close()
        return redirect(url_for(
            'customer_products',
            error_product=product_id,
            error_msg="Product not found"
        ))

    if quantity > product['available_quantity']:
        cursor.close()
        db.close()
        return redirect(url_for(
            'customer_products',
            error_product=product_id,
            error_msg=f"Only {product['available_quantity']} available"
        ))

    cursor.execute("""
    UPDATE branch_Product
    SET available_quantity = available_quantity - %s
    WHERE product_id = %s
      AND branch_id = %s
      AND available_quantity >= %s
    """, (quantity, product_id, branch_id, quantity))


    cursor.execute(
        """select cart_id
            from Cart
            where customer_id = %s AND branch_id = %s
            """,
        (customer_id,branch_id)
    )
    cart = cursor.fetchone()

    if not cart:
        cursor.execute(
            """INSERT INTO Cart (customer_id, branch_id, creation_time)
            VALUES (%s, %s, NOW())""",
            (customer_id,branch_id)
        )
        cart_id = cursor.lastrowid
    else:
        cart_id = cart['cart_id']

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

    return redirect(url_for('customer_products', added=product_id))



@app.route('/customer_cart')
def customer_cart():
    cart_branch = request.args.get('branch_id')

    if cart_branch:
        session['cart_view_branch'] = cart_branch
    #  their is a defualt branch selected which is the main branch in ramallah
    branch_id = session.get('cart_view_branch') or session.get('selected_branch')

    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # cart items
    cursor.execute("""
         select 
        p.product_id,
        p.product_name,
        p.price,
        cp.quantity,
        (p.price * cp.quantity) as total
    from Cart c
    join cart_product cp on c.cart_id = cp.cart_id
    join Product p on cp.product_id = p.product_id
    where c.customer_id = %s and c.branch_id = %s
    """, (customer_id,branch_id))
    cart_items = cursor.fetchall()

    total_price = sum(item['total'] for item in cart_items)

    # products for add form
    cursor.execute("""
        select product_id, product_name
        from Product
        where available_quantity > 0
    """)
    products = cursor.fetchall()
    cursor.execute("""
    select branch_id, branch_name
    from branch
    where branch_status in ('ACTIVE','OPEN')
""")
    branches = cursor.fetchall()


    cursor.close()
    db.close()

    return render_template(
        'customer_cart.html',
         cart_items=cart_items,
         total_price=total_price,
         branches = branches,
         current_branch= branch_id

    )


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']
    product_id = request.form['product_id']
    branch_id = session.get('selected_branch')

    db = get_db()
    cursor = db.cursor(dictionary=True)
    # get the quantity of the product
    cursor.execute("""
        select cp.quantity
        from cart_product cp
        join Cart c on cp.cart_id = c.cart_id
        where c.customer_id = %s
          and c.branch_id = %s
          and cp.product_id = %s
    """, (customer_id, branch_id, product_id))

    item = cursor.fetchone()

    if item:
        removed_qty = item['quantity']

        #  upddate the stock in the branch 
        cursor.execute("""
            update branch_Product
            set available_quantity = available_quantity + %s
            where product_id = %s AND branch_id = %s
        """, (removed_qty, product_id, branch_id))
# delete products from cart
        cursor.execute("""
            delete cp FROM cart_product cp
            join Cart c on cp.cart_id = c.cart_id
            where c.customer_id = %s
              and c.branch_id = %s
              and cp.product_id = %s
        """, (customer_id, branch_id, product_id))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('customer_cart'))


@app.route('/checkout', methods=['POST'])
def checkout():
    if 'customer_id' not in session:
        return redirect(url_for('customer'))

    customer_id = session['customer_id']
    branch_id = session.get('selected_branch')

    payment_method = request.form['payment_method']

    db = get_db()
    cursor = db.cursor(dictionary=True)
# get the products from the cart
    cursor.execute("""
        select p.product_id, p.price, cp.quantity, (p.price * cp.quantity) as total
        from Cart c
        join cart_product cp on c.cart_id = cp.cart_id
        join Product p on cp.product_id = p.product_id
        where c.customer_id = %s and c.branch_id = %s

    """, (customer_id,branch_id))
    cart_items = cursor.fetchall()

    if not cart_items:
        cursor.close()
        db.close()
        return redirect(url_for('customer_cart'))

    total_amount = sum(item['total'] for item in cart_items)


    cursor.execute("""
    select count(*) as num_invoices
    from sales_invoice
    where customer_id = %s and branch_id = %s
    """, (customer_id, branch_id))

    result = cursor.fetchone()
    next_invoice_num = result['num_invoices'] + 1
    from datetime import datetime
    invoice_date = datetime.now()
    formatted_customer_id = format_customer_id(customer_id)


    while True:
        invoice_id = f"{customer_id}-{next_invoice_num:04d}"

        try:
            

            cursor.execute("""
            insert into sales_invoice
            (invoice_id, customer_id, branch_id, invoice_date, total_amount, payment_method)
            values (%s, %s, %s, %s, %s, %s)
            """, (invoice_id, customer_id, branch_id, invoice_date, total_amount, payment_method))

            break  # كلشي تمام

        except mysql.connector.errors.IntegrityError as e:
            if e.errno == 1062:   # dupli PK
                next_invoice_num += 1  # جرب  رقم جديد
            else:
                raise  # أي خطأ غير هيك خليه يطلع

    # add products on duplicate 
    for item in cart_items:
        cursor.execute("""
            insert into invoice_product (invoice_id, product_id, quantity)
            values (%s, %s, %s)
            on duplicate key update quantity = quantity + values(quantity)
        """, (invoice_id, item['product_id'], item['quantity']))

# empty the cart 
    cursor.execute("""
        delete cp from cart_product cp
        join Cart c on cp.cart_id = c.cart_id
        where customer_id = %s and branch_id = %s

    """, (customer_id,branch_id))
    cursor.execute("delete from Cart where customer_id=%s and branch_id=%s", (customer_id,branch_id))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('customer_invoice', invoice_id=invoice_id))

@app.route('/customer_invoice/<invoice_id>')
def customer_invoice(invoice_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    #select the products from the invois 
    cursor.execute("""
        select p.product_name, p.price, ip.quantity,
               (p.price * ip.quantity) as total
        from invoice_product ip
        join Product p on ip.product_id = p.product_id
        where ip.invoice_id = %s
    """, (invoice_id,))
    items = cursor.fetchall()

    #select the invoice data with branch name and location with paymint method 
    cursor.execute("""
        select si.invoice_id, si.payment_method, b.branch_name, b.branch_location
        from sales_invoice si
        join branch b on si.branch_id = b.branch_id
        where si.invoice_id = %s
    """, (invoice_id,))
    invoice_info = cursor.fetchone()

    total = sum(i['total'] for i in items)

    cursor.close()
    db.close()

    return render_template(
        'customer_invoice.html',
        cart_items=items,
        total_price=total,
        branch_name=invoice_info['branch_name'],
        branch_location=invoice_info['branch_location'],
        payment_method=invoice_info['payment_method']
    )

# requests management

@app.route('/request_reorder', methods=['POST'])
def request_reorder():
    if 'employee_id' not in session or session.get('category') != 'branchEmployee':
        return redirect(url_for('employee'))

    employee_id = session['employee_id']
    product_id = request.form['product_id']
    request_quantity = int(request.form['quantity'])

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get branch and warehouse info
    cursor.execute("select branch_id from Employee where employee_id = %s", (employee_id,))
    branch_id = cursor.fetchone()['branch_id']
    
    cursor.execute("select warehouse_id from Warehouse where branch_id = %s", (branch_id,))
    warehouse_result = cursor.fetchone()
    
    if not warehouse_result:
        cursor.close()
        db.close()
        return "No warehouse assigned to this branch", 400
        
    warehouse_id = warehouse_result['warehouse_id']

    # get branch manager
    cursor.execute("select manager_id from Manager where branch_id = %s and category = 'branchManager'", (branch_id,))
    manager_result = cursor.fetchone()
    branch_manager_id = manager_result['manager_id'] if manager_result else None

    # insert order request
    cursor.execute("""
        insert into OrderRequest (product_id, branch_id, warehouse_id, employee_id, branch_manager_id, request_quantity, req_status)
        value (%s, %s, %s, %s, %s, %s, 'PENDING_BRANCH_MANAGER')
    """, (product_id, branch_id, warehouse_id, employee_id, branch_manager_id, request_quantity))

    request_id = cursor.lastrowid

    # get product name
    cursor.execute("select product_name from Product where product_id = %s", (product_id,))
    product_name = cursor.fetchone()['product_name']

    # notify branch manager
    if branch_manager_id:
        cursor.execute("""
            insert into Notification (manager_id, notification_type, message, related_id)
            values (%s, 'request_pending_action', %s, %s)
        """, (branch_manager_id, 
              f"New reorder request #{request_id} for {product_name} ({request_quantity} items) from employee {employee_id}",
              str(request_id)))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('branch_employee_dashboard'))

@app.route('/branch_manager_handle_request', methods=['POST'])
def branch_manager_handle_request():
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager'))
    
    manager_id = session['manager_id']
    request_id = request.form['request_id']
    action = request.form['action']  # approve or reject
    notes = request.form.get('notes', '')
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # get request details
    cursor.execute("""
        select r.*, p.product_name, wp.available_quantity as warehouse_qty
        from OrderRequest r
        join Product p on r.product_id = p.product_id
        left join warehouse_Product wp on r.warehouse_id = wp.warehouse_id and r.product_id = wp.product_id
        where r.request_id = %s
    """, (request_id,))
    req = cursor.fetchone()
    
    if not req:
        cursor.close()
        db.close()
        return "Request not found", 404
    
    if action == 'reject':
        # reject the request
        cursor.execute("""
            update OrderRequest 
            set req_status = 'REJECTED', 
                branch_manager_response_date = NOW(),
                rejection_reason = %s,
                notes = %s
            where request_id = %s
        """, (notes, notes, request_id))
        
        # notify employee
        cursor.execute("""
            insert intp Notification (employee_id, notification_type, message, related_id)
            values ( %s, 'request_rejected', %s, %s)
        """, (req['employee_id'], 
              f"Your reorder request #{request_id} for {req['product_name']} was rejected. Reason: {notes}",
              str(request_id)))
        
    else:  # approve
        warehouse_qty = req.get('warehouse_qty', 0) or 0
        
        if warehouse_qty >= req['request_quantity']:
            # warehouse has enough stock - send to warehouse employees
            cursor.execute("""
                update OrderRequest 
                set req_status = 'PENDING_WAREHOUSE_EMPLOYEE',
                    branch_manager_response_date = NOW(),
                    notes = %s
                where request_id = %s
            """, (notes, request_id))
            
            # notify warehouse employees
            cursor.execute("""
                select employee_id from Employee 
                where warehouse_id = %s and category = 'warehouseEmployee'
            """, (req['warehouse_id'],))
            warehouse_employees = cursor.fetchall()
            
            for emp in warehouse_employees:
                cursor.execute("""
                    insert into Notification (employee_id, notification_type, message, related_id)
                    values ( %s, 'request_pending_action', %s, %s)
                """, (emp['employee_id'], 
                      f"New transfer request #{request_id}: Move {req['request_quantity']} items of {req['product_name']} to Branch {req['branch_id']}",
                      str(request_id)))
            
        else:
            # warehouse doesnt have enough,send to warehouse manager
            cursor.execute("""
                update OrderRequest 
                set req_status = 'PENDING_WAREHOUSE_MANAGER',
                    branch_manager_response_date = NOW(),
                    notes = %s
                where request_id = %s
            """, (f"Not Enough Product Amount In Warehouse ({warehouse_qty}/{req['request_quantity']}). {notes}", request_id))
            
            # get warehouse manager
            cursor.execute("""
                select manager_id from Manager 
                where warehouse_id = %s and category = 'warehouseManager'
            """, (req['warehouse_id'],))
            wh_manager = cursor.fetchone()
            
            if wh_manager:
                cursor.execute("""
                    insert into Notification (manager_id, notification_type, message, related_id)
                    values (%s, 'request_pending_action', %s, %s)
                """, (wh_manager['manager_id'], 
                      f"Purchase needed: Request #{request_id} for {req['request_quantity']} items of {req['product_name']} (Current stock: {warehouse_qty})",
                      str(request_id)))
                
                # update warehouse_manager_id in request
                cursor.execute("""
                    update OrderRequest set warehouse_manager_id = %s where request_id = %s
                """, (wh_manager['manager_id'], request_id))
    
    db.commit()
    cursor.close()
    db.close()
    
    return redirect(url_for('branch_manager_dashboard'))

@app.route('/warehouse_employee_handle_request', methods=['POST'])
def warehouse_employee_handle_request():
    if 'employee_id' not in session or session.get('category') != 'warehouseEmployee':
        return redirect(url_for('employee'))
    
    employee_id = session['employee_id']
    request_id = request.form['request_id']
    action = request.form['action']  # 'approve' or 'reject'
    notes = request.form.get('notes', '')
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # get request details
    cursor.execute("""
        select r.*, p.product_name
        from OrderRequest r
        join Product p ON r.product_id = p.product_id
        where r.request_id = %s
    """, (request_id,))
    req = cursor.fetchone()
    
    if action == 'reject':
        cursor.execute("""
            update OrderRequest 
            set req_status = 'REJECTED',
                warehouse_response_date = NOW(),
                rejection_reason = %s
            where request_id = %s
        """, (notes, request_id))
        
        message = f"Transfer request #{request_id} for {req['product_name']} was rejected by warehouse. Reason: {notes}"
        
    else:  # approve
        # transfer stock from warehouse to branch
        cursor.execute("""
            update warehouse_Product 
            set available_quantity = available_quantity - %s
            where warehouse_id = %s and product_id = %s and available_quantity >= %s
        """, (req['request_quantity'], req['warehouse_id'], req['product_id'], req['request_quantity']))
        
        cursor.execute("""
            update branch_Product 
            set available_quantity = available_quantity + %s
            where branch_id = %s and product_id = %s
        """, (req['request_quantity'], req['branch_id'], req['product_id']))
        
        cursor.execute("""
            update OrderRequest 
            set req_status = 'APPROVED',
                warehouse_response_date = NOW(),
                notes = %s
            where request_id = %s
        """, (notes, request_id))
        
        message = f"Your reorder request #{request_id} for {req['product_name']} has been approved and stock transferred"
    
    # notify branch employee and manager
        cursor.execute("""
        INSERT INTO Notification (employee_id, notification_type, message, related_id)
        VALUES (%s, %s, %s, %s)
        """, (
        req['employee_id'],
    'request_approved' if action == 'approve' else 'request_rejected',
    message,
    str(request_id)
))

    
# notify manager
    if req['branch_manager_id']:
        cursor.execute("""
            insert into Notification (manager_id, notification_type, message, related_id)
            values (%s, %s, %s, %s)
        """, (req['branch_manager_id'],
          'request_approved' if action == 'approve' else 'request_rejected',
          message, str(request_id)))
    
    db.commit()
    cursor.close()
    db.close()
    
    return redirect(url_for('Warehouse_employee_Dashboard'))


@app.route('/warehouse_manager_handle_request', methods=['POST'])
def warehouse_manager_handle_request():
    if 'manager_id' not in session or session.get('category') != 'warehouseManager':
        return redirect(url_for('manager'))

    request_id = request.form['request_id']
    action = request.form['action']

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # get request details
    cursor.execute("""
        select r.*, p.product_name, p.price
        from OrderRequest r
        join Product p on r.product_id = p.product_id
        where r.request_id = %s
    """, (request_id,))
    req = cursor.fetchone()

    if not req:
        cursor.close()
        db.close()
        return redirect(url_for('warehouse_manager_dashboard'))

    # rejected 
    if action == 'reject':
        notes = request.form.get('notes', '')

        cursor.execute("""
            update OrderRequest
            set req_status = 'REJECTED',
                rejection_reason = %s,
                warehouse_response_date = NOW()
            where request_id = %s
        """, (notes, request_id))

        message = f"Purchase request #{request_id} rejected. Reason: {notes}"

    # purchase
    else:
        supplier_id = request.form['supplier_id']
        request_quantity = int(request.form['reqeust_quantity'])
        
        # Calculate total cost: price * quantity
        total_cost = req['price'] * request_quantity

        # random status
        random_value = random.choice([0, 1])
        order_status = 'ON-WAY' if random_value == 1 else 'DONE'

        # generate Purchase Order ID
        cursor.execute("""
            select IFNULL(max(CAST(SUBSTRING(order_id, 3) AS UNSIGNED)), 0) + 1 as next_id
            from Purchase_Order
        """)
        next_id = int(cursor.fetchone()['next_id'])
        order_id = f"PO{next_id:04d}"

        # insert purchase order WITH order_cost
        cursor.execute("""
            insert into Purchase_Order
            (order_id, supplier_id, warehouse_id, order_date,
             order_status, product_id, product_quantity, order_cost)
            values (%s, %s, %s, NOW(), %s, %s, %s, %s)
        """, (
            order_id,
            supplier_id,
            req['warehouse_id'],
            order_status,
            req['product_id'],
            request_quantity,
            total_cost
        ))

        # Add warehouse-supplier relationship (if not already exists)
        cursor.execute("""
            insert ignore into supplier_warehouse (supplier_id, warehouse_id)
            values (%s, %s)
        """, (supplier_id, req['warehouse_id']))

        # if done, add quantity to warehouse (not branch!)
        if order_status == 'DONE':
            # Add to warehouse first
            cursor.execute("""
                insert into warehouse_Product (warehouse_id, product_id, available_quantity)
                values (%s, %s, %s)
                on duplicate key update
                available_quantity = available_quantity + values(available_quantity)
            """, (
                req['warehouse_id'],
                req['product_id'],
                request_quantity
            ))
            
            # Then transfer to branch if warehouse now has enough
            cursor.execute("""
                select available_quantity from warehouse_Product
                where warehouse_id = %s and product_id = %s
            """, (req['warehouse_id'], req['product_id']))
            
            wh_stock = cursor.fetchone()
            
            if wh_stock and wh_stock['available_quantity'] >= req['request_quantity']:
                # Transfer to branch
                cursor.execute("""
                    update warehouse_Product
                    set available_quantity = available_quantity - %s
                    where warehouse_id = %s and product_id = %s
                """, (req['request_quantity'], req['warehouse_id'], req['product_id']))
                
                cursor.execute("""
                    insert into branch_Product (branch_id, product_id, available_quantity)
                    values (%s, %s, %s)
                    on duplicate key update
                    available_quantity = available_quantity + values(available_quantity)
                """, (
                    req['branch_id'],
                    req['product_id'],
                    req['request_quantity']
                ))

        # update request
        cursor.execute("""
            update OrderRequest
            set req_status = 'APPROVED',
                warehouse_response_date = NOW(),
                notes = CONCAT(IFNULL(notes,''), ' | Purchase Order ', %s, ' ', %s, ' - Cost: $', %s)
            where request_id = %s
        """, (order_id, order_status, total_cost, request_id))

        message = (
            f"Purchase Order {order_id} created "
            f"({order_status}) for {request_quantity} items of {req['product_name']} - Total Cost: ${total_cost:.2f}"
        )

    # notify manager
    if req['branch_manager_id']:
        cursor.execute("""
            insert into Notification
            (manager_id, notification_type, message, related_id)
            values (%s, %s, %s, %s)
        """, (
            req['branch_manager_id'],
            'purchase_order_created' if action == 'purchase' else 'request_rejected',
            message,
            request_id
        ))

    # notify employee
    if req['employee_id']:
        cursor.execute("""
            insert into Notification
            (employee_id, notification_type, message, related_id)
            values (%s, %s, %s, %s)
        """, (
            req['employee_id'],
            'purchase_order_created' if action == 'purchase' else 'request_rejected',
            message,
            request_id
        ))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for('warehouse_manager_dashboard'))
# route to reject reorder request

@app.route('/reject_reorder_request', methods=['POST'])
def reject_reorder_request():
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager'))
    
    manager_id = session['manager_id']
    request_id = request.form['request_id']
    rejection_notes = request.form.get('rejection_notes', '')
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # get employee_id
    cursor.execute("""
        select employee_id from Reorder_Request WHERE request_id = %s
    """, (request_id,))
    req = cursor.fetchone()
    
    # update request status
    cursor.execute("""
        update Reorder_Request 
        set request_status = 'REJECTED', 
            manager_id = %s,
            response_date = NOW(),
            notes = CONCAT(IFNULL(notes, ''), ' | Manager note: ', %s)
        where request_id = %s
    """, (manager_id, rejection_notes, request_id))
    
    # create notification for employee
    cursor.execute("""
        insert into Notification 
        (employee_id, notification_type, message, related_id)
        values ( %s, 'request_rejected', %s, %s)
    """, (req['employee_id'], 
          f"Your reorder request #{request_id} has been rejected. Reason: {rejection_notes}",
          str(request_id)))
    
    db.commit()
    cursor.close()
    db.close()
    
    return redirect(url_for('Branch_Manager_Dashboard'))


@app.route('/mark_notification_read/<int:notification_id>')
def mark_notification_read(notification_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("""
        update Notification set is_read = TRUE where notification_id = %s
    """, (notification_id,))
    
    db.commit()
    cursor.close()
    db.close()
    
    return redirect(request.referrer or url_for('home'))


@app.route('/branch_customer_sales')
def branch_customer_sales():
    if 'employee_id' not in session or session.get('category') != 'branchEmployee':
        return redirect(url_for('employee'))
    
    branch_id = session['branch_id']
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # Get branch information
    cursor.execute("""
        select branch_name, branch_location
        from Branch
        where branch_id = %s
    """, (branch_id,))
    branch_info = cursor.fetchone()
    
    # get all customers with invoices in this branch
    cursor.execute("""
        select distinct
            c.customer_id,
            p.person_name,
            p.phone_num,
            p.address
        from Customer c
        join Person p on c.person_id = p.person_id
        join sales_invoice si on c.customer_id = si.customer_id
        where si.branch_id = %s
        order by p.person_name
    """, (branch_id,))
    customers = cursor.fetchall()
    
    # for each customer, get their invoices and total sales
    customer_sales_data = []
    
    for customer in customers:
        customer_id = customer['customer_id']
        formatted_customer_id = format_customer_id(customer_id)
        # Get all invoices for this customer at this branch
        cursor.execute("""
            select 
                invoice_id,
                invoice_date,
                total_amount,
                payment_method
            from sales_invoice
            where customer_id = %s and branch_id = %s
            order by invoice_date DESC
        """, (customer_id, branch_id))
        invoices = cursor.fetchall()
        
        # calculate total sales for this customer
        cursor.execute("""
            select 
                count(*) as total_invoices,
                sum(total_amount) as total_sales
            from sales_invoice
            where customer_id = %s AND branch_id = %s
        """, (customer_id, branch_id))
        sales_summary = cursor.fetchone()
        
        customer_sales_data.append({
            'customer_id': customer['customer_id'],
            'customer_name': formatted_customer_id,
            'phone': customer['phone_num'],
            'address': customer['address'],
            'invoices': invoices,
            'total_invoices': sales_summary['total_invoices'],
            'total_sales': sales_summary['total_sales'] or 0
        })
    
    # calculate overall branch statistics
    cursor.execute("""
        SELECT 
            count(distinct customer_id) as total_customers,
            count(*) as total_invoices,
            sum(total_amount) as total_revenue
        from sales_invoice
        where branch_id = %s
    """, (branch_id,))
    branch_stats = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template(
        'branch_costumers_emp.html',
        branch_info=branch_info,
        customer_sales_data=customer_sales_data,
        branch_stats=branch_stats
    )


@app.route('/branch_manager_customer_sales')
def branch_manager_customer_sales():
    if 'manager_id' not in session or session.get('category') != 'branchManager':
        return redirect(url_for('manager'))
    
    branch_id = session['branch_id']
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # get branch information
    cursor.execute("""
        select branch_name, branch_location
        from Branch
        where branch_id = %s
    """, (branch_id,))
    branch_info = cursor.fetchone()
    
    # get all customers with invoices in this branch
    cursor.execute("""
        select distinct
            c.customer_id,
            p.person_name,
            p.phone_num,
            p.address
        from Customer c
        join Person p on c.person_id = p.person_id
        join sales_invoice si on c.customer_id = si.customer_id
        where si.branch_id = %s
        order by p.person_name
    """, (branch_id,))
    customers = cursor.fetchall()
    
    # for each customer, get their invoices and total sales
    customer_sales_data = []
    
    for customer in customers:
        customer_id = customer['customer_id']
        formatted_customer_id = format_customer_id(customer_id)

        # get all invoices for this customer at this branch
        cursor.execute("""
            select 
                invoice_id,
                invoice_date,
                total_amount,
                payment_method
            from sales_invoice
            where customer_id = %s and branch_id = %s
            order by invoice_date DESC
        """, (customer_id, branch_id))
        invoices = cursor.fetchall()
        
        # calculate total sales for this customer
        cursor.execute("""
            select 
                count(*) as total_invoices,
                sum(total_amount) as total_sales
            from sales_invoice
            where customer_id = %s and branch_id = %s
        """, (customer_id, branch_id))
        sales_summary = cursor.fetchone()
        
        customer_sales_data.append({
            'customer_id': customer['customer_id'],
            'formatted_customer_id': formatted_customer_id,
            'phone': customer['phone_num'],
            'address': customer['address'],
            'invoices': invoices,
            'total_invoices': sales_summary['total_invoices'],
            'total_sales': sales_summary['total_sales'] or 0
        })
    
    # calculate overall branch statistics
    cursor.execute("""
        select 
            count(distinct customer_id) as total_customers,
            count(*) as total_invoices,
            sum(total_amount) as total_revenue
        from sales_invoice
        where branch_id = %s
    """, (branch_id,))
    branch_stats = cursor.fetchone()
    
    # get top customers by sales
    cursor.execute("""
        select 
            c.customer_id,
            p.person_name,
            count(*) as invoice_count,
            sum(si.total_amount) as total_spent
        from sales_invoice si
        join Customer c on si.customer_id = c.customer_id
        join Person p on c.person_id = p.person_id
        where si.branch_id = %s
        group by c.customer_id, p.person_name
        order by total_spent DESC
        limit 5
    """, (branch_id,))
    top_customers = cursor.fetchall()
    
    for cust in top_customers:
        cust['formatted_customer_id'] = format_customer_id(cust['customer_id'])
    
    # Get sales by payment method
    cursor.execute("""
        select  
            payment_method,
            count(*) as count,
            sum(total_amount) as total
        from sales_invoice
        where branch_id = %s
        group by payment_method
    """, (branch_id,))
    payment_stats = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template(
        'branch_costumers_mang.html',
        branch_info=branch_info,
        customer_sales_data=customer_sales_data,
        branch_stats=branch_stats,
        top_customers=top_customers,
        payment_stats=payment_stats
    )

# helper functions for ID formatting
def format_employee_id(employee_id, category):
    """format employee ID based on category"""
    if category == 'branchEmployee':
        return f"BE{employee_id}"
    elif category == 'warehouseEmployee':
        return f"WE{employee_id}"
    return str(employee_id)

def format_manager_id(manager_id, category):
    """format manager ID  based on category"""
    if category == 'branchManager':
        return f"BM{manager_id}"
    elif category == 'warehouseManager':
        return f"WM{manager_id}"
    return str(manager_id)

def format_customer_id(customer_id):
    """format customer ID with C """
    return f"C{customer_id}"

def parse_employee_id(formatted_id):
    """extract numeric ID from employee ID"""
    if formatted_id.startswith('BE') or formatted_id.startswith('WE'):
        return int(formatted_id[2:])
    return int(formatted_id)

def parse_manager_id(formatted_id):
    """extract numeric ID from manager ID"""
    if formatted_id.startswith('BM') or formatted_id.startswith('WM'):
        return int(formatted_id[2:])
    return int(formatted_id)

def parse_customer_id(formatted_id):
    """extract numeric ID from customer ID"""
    if formatted_id.startswith('C'):
        return int(formatted_id[1:])
    return int(formatted_id)
    
@app.route('/generate_employee_id')
def generate_employee_id():
    """auto generate the next branch employee id """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # get the last employee_id and add 1
    cursor.execute("select max(employee_id) as last_id from Employee")
    result = cursor.fetchone()
    next_id = (result['last_id'] + 1) if result and result['last_id'] else 1
    
    cursor.close()
    db.close()
    
    # format as BE (Branch Employee)
    formatted_id = f"BE{next_id}"
    return jsonify({"employee_id": formatted_id})

@app.route('/generate_warehouse_employee_id')
def generate_warehouse_employee_id():
    """auto generate the next warehouse employee id """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    # get the last employee_id and add 1
    cursor.execute("select max(employee_id) as last_id from Employee")
    result = cursor.fetchone()
    next_id = (result['last_id'] + 1) if result and result['last_id'] else 1
    
    cursor.close()
    db.close()
    
    # format as WE (Warehouse Employee)
    formatted_id = f"WE{next_id}"
    return jsonify({"employee_id": formatted_id})

if __name__ == "__main__":
    app.run(debug=True)
