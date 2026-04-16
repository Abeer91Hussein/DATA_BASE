use salehkalaf;
#Start------------- Appliying the erd diagram with all of it relations --------------------
#tables for this database 

CREATE TABLE Person(
 person_id INT,
 person_name varchar(16),
 phone_num decimal(10),
 address varchar(32),
 primary key (person_id)
 );
 
Create table supplier(
supplier_id varchar(16),
supplier_name varchar(32),
phone_num decimal(10),
address varchar(32),
email varchar(16) unique not null,
primary key(supplier_id)
);

CREATE TABLE branch (
    branch_id INT PRIMARY KEY,
    branch_name VARCHAR(32),
    branch_location VARCHAR(60) not null,
    branch_status ENUM('ACTIVE','OPEN','CLOSED','UNDER-REPAIR') NOT NULL,
    branch_capacity INT not null
);
alter table branch
add column branch_phoneNum varchar(15);


 create table Product(
product_id varchar(16),
product_name varchar(16),
product_status ENUM('available','OutOfStock') not null,
imported_quantity  INT,
available_quantity INT,
reOrder_level INT,
price decimal(5,2),
production_date DATE,
expired_date Date,
product_category varchar(32),
product_discretion varchar(300),#product description
 product_unit ENUM('Liter','GRAM','KG','PIECE','BOX') not null,
 primary key (product_id)
);



CREATE TABLE Employee(
 person_id INT,
 employee_id varchar(16),
 category ENUM('branchEmployee','warehouseEmployee') not null,
salary INT,
branch_id INT,
warehouse_id varchar(16),
primary key (employee_id),
foreign key (person_id) references Person(person_id),
foreign key (branch_id) references Branch(branch_id),
foreign key (warehouse_id) references warehouse(warehouse_id)
 );


alter table Employee
add column password varchar(255);

CREATE TABLE Manager(
manager_id varchar(16),
person_id INT,
category ENUM('branchManager','warehouseManager') not null,
salary INT,
branch_id INT unique,
warehouse_id varchar(16) unique,

primary key (manager_id),
foreign key (person_id) references Person(person_id),
foreign key (branch_id) references Branch(branch_id),
foreign key (warehouse_id) references Warehouse(warehouse_id)
);


alter table Manager
add column password varchar(255);


CREATE TABLE Customer(
customer_id varchar(16),
person_id INT,
primary key (customer_id),
foreign key (person_id) references Person(person_id)
);


alter table Customer
add column password varchar(255);


create table Warehouse(
warehouse_id varchar(16) ,
branch_id INT unique,
warehouse_location varchar(32),
warehouse_capacity INT, 
warehouse_status ENUM ('ACTIVE','OPEN','CLOSED','UNDER-REPAIR') NOT NULL, 
primary key (warehouse_id),
foreign key (branch_id) references Branch(branch_id)  
);
alter table Warehouse
add column warehouse_PhoneNum varchar(15);
 
create table Cart(
cart_id INT auto_increment,
customer_id varchar(16),
creation_time Time ,
primary key(cart_id),
foreign key (customer_id) references Customer(customer_id));


#tables for sales in this database 
CREATE TABLE sales_invoice (
    invoice_id VARCHAR(16) PRIMARY KEY,
    customer_id VARCHAR(16),
    branch_id INT,
    invoice_date DATETIME,
    total_amount DECIMAL(10,2),
    payment_method ENUM('CASH/ONARRIVAL','PAYPAL','VISA','DEBITCARD') NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (branch_id) REFERENCES Branch(branch_id)
);

Create table Purchase_Order(
order_id varchar(16),
supplier_id varchar(16),
warehouse_id varchar(16),
order_date date,
order_status ENUM ('DONE','ON-WAY')NOT NULL,
order_cost decimal (10,2),
product_id varchar(16),
product_quantity int,
primary key (order_id),
foreign key (supplier_id) references Supplier(supplier_id),
foreign key (warehouse_id) references Warehouse(warehouse_id),
foreign key (product_id) references Product(product_id)
);

#tables dor many-many relationships 
# invoice - product 
CREATE TABLE invoice_product (
    invoice_id VARCHAR(16),
    product_id VARCHAR(16),
    quantity INT NOT NULL,
    PRIMARY KEY (invoice_id, product_id),
    FOREIGN KEY (invoice_id) REFERENCES Sales_invoice(invoice_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);
#warehouse - product 
CREATE Table warehouse_Product (
warehouse_id VARCHAR(16),
product_id VARCHAR(16),
PRIMARY key (warehouse_id, product_id),
FOREIGN key (warehouse_id) REFERENCES Warehouse(warehouse_id),
FOREIGN key (product_id) REFERENCES Product(product_id)
);
alter table branch_product
add column  available_quantity int;

#supplier - product 
CREATE TABLE supplier_product (
    supplier_id VARCHAR(16),
    product_id VARCHAR(16),
    PRIMARY KEY (supplier_id , product_id),
    FOREIGN KEY (product_id)
        REFERENCES Product (product_id),
    FOREIGN KEY (supplier_id)
        REFERENCES Supplier (supplier_id)
);

#supplier - warehouse
create table supplier_warehouse(
supplier_id varchar(16),
warehouse_id varchar(16),
primary key (supplier_id,warehouse_id),
FOREIGN key (warehouse_id) REFERENCES Warehouse(warehouse_id),
foreign key  (supplier_id) REFERENCES Supplier(supplier_id)
);

#cart - product 
create table cart_product(
cart_id INT , 
product_id varchar(16),
quantity INT not null,
primary key (cart_id, product_id),
foreign key(product_id) references Product(product_id),
foreign key(cart_id) references Cart(cart_id));

# branch - product
CREATE TABLE branch_Product (
    branch_id INT,
    product_id VARCHAR(16),
    quantity INT NOT NULL DEFAULT 0,
    reorder_level_branch INT NOT NULL DEFAULT 5, 
    PRIMARY KEY (branch_id, product_id),
    FOREIGN KEY (branch_id) REFERENCES Branch(branch_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE OrderRequest (
    request_id INT AUTO_INCREMENT,
    product_id VARCHAR(16),
    branch_id INT,
    warehouse_id VARCHAR(16),
    employee_id VARCHAR(16),
    branch_manager_id VARCHAR(16),
    warehouse_manager_id VARCHAR(16),
    request_quantity INT NOT NULL,
    request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    branch_manager_response_date DATETIME,
    warehouse_response_date DATETIME,
    req_status ENUM('PENDING_BRANCH_MANAGER', 'PENDING_WAREHOUSE_EMPLOYEE', 'PENDING_WAREHOUSE_MANAGER', 'APPROVED', 'REJECTED') DEFAULT 'PENDING_BRANCH_MANAGER',
    rejection_reason VARCHAR(300),
    notes VARCHAR(300),
    PRIMARY KEY (request_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    FOREIGN KEY (branch_id) REFERENCES Branch(branch_id),
    FOREIGN KEY (warehouse_id) REFERENCES Warehouse(warehouse_id),
    FOREIGN KEY (employee_id) REFERENCES Employee(employee_id),
    FOREIGN KEY (branch_manager_id) REFERENCES Manager(manager_id),
    FOREIGN KEY (warehouse_manager_id) REFERENCES Manager(manager_id)
);

CREATE TABLE Notification (
    notification_id INT AUTO_INCREMENT,
    
    employee_id VARCHAR(16) NULL,
    manager_id VARCHAR(16) NULL,

    notification_type ENUM(
        'reorder_alert',
        'request_created',
        'request_approved',
        'request_rejected',
        'request_pending_action',
        'purchase_order_created'
    ) NOT NULL,

    message VARCHAR(500) NOT NULL,
    related_id VARCHAR(16),
    is_read BOOLEAN DEFAULT FALSE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (notification_id),

    FOREIGN KEY (employee_id) REFERENCES Employee(employee_id),
    FOREIGN KEY (manager_id) REFERENCES Manager(manager_id)

    
);

#######################################################################################





INSERT INTO Person (person_id, person_name, phone_num, address)
VALUES (1, 'Noor', 0591234567, 'Ramallah');

INSERT INTO Customer (customer_id, person_id, password)
VALUES ('C001', 1, 'mypassword123');

INSERT INTO branch (branch_id, branch_name, branch_location,branch_status, branch_capacity,branch_phoneNum)
VALUES (1,'Main Branch'	,'Ramallah'	,'OPEN'	,500,	'059598989');

INSERT INTO branch (branch_id, branch_name, branch_location,branch_status, branch_capacity,branch_phoneNum)
VALUES (2,'second branch','Tulkarim','OPEN'	,500,	'059599998');


INSERT INTO warehouse (warehouse_id, branch_id, warehouse_location,warehouse_status, warehouse_capacity,warehouse_phoneNum)
VALUES ('WH01',	1,'Ramallah'	,'OPEN'	,500,	'059598989');


INSERT INTO warehouse (warehouse_id, branch_id, warehouse_location,warehouse_status, warehouse_capacity,warehouse_phoneNum)
VALUES ('WH02',	2,'Gaza','OPEN'	,500,	'059598989');



INSERT INTO Employee (employee_id, person_id, category, salary, branch_id, warehouse_id, password)
VALUES ('E001', 1, 'branchEmployee', 1200, 1, 'WH01', 'mypassword123');

INSERT INTO Manager (manager_id, person_id, category, salary, branch_id, warehouse_id, password)
VALUES ('M001', 1, 'branchManager', 2000, 1, 'WH01', 'mypassword123');


INSERT INTO Person (person_id, person_name, phone_num, address) VALUES
(2, 'Fatima Ali', 0592345678, 'Nablus, Old City'),
(3, 'Mohammed Khaled', 0593456789, 'Hebron, Downtown'),
(4, 'Sara Ibrahim', 0594567890, 'Bethlehem, Beit Jala'),
(5, 'Omar Yousef', 0595678901, 'Jenin, City Center'),
(6, 'Layla Ahmad', 0596789012, 'Ramallah, Tireh'),
(7, 'Kareem Nasser', 0597890123, 'Tulkarem, East'),
(8, 'Noor Salem', 0598901234, 'Qalqilya, North');


-- Branch Manager (will get ID = 1as BM1)
INSERT INTO Manager (person_id, category, salary, branch_id, warehouse_id, password)
VALUES (1, 'branchManager', 3000, 1, NULL, '123456');

INSERT INTO Person (person_id, person_name, phone_num, address)
VALUES (14, 'Noor', 0591234567, 'Ramallah');

INSERT INTO Manager (person_id, category, salary, branch_id, warehouse_id, password)
VALUES (14, 'branchManager', 3000, 2, NULL, '123456');

-- Warehouse Manager (will get ID = 2 as WM2)
INSERT INTO Manager (person_id, category, salary, branch_id, warehouse_id, password)
VALUES (2, 'warehouseManager', 3500, NULL, 'WH01', '123456');

 
-- Branch Employees (will get IDs 1,2,3 as BE1, BE2, BE3)
INSERT INTO Employee (person_id, category, salary, branch_id, warehouse_id, password)
VALUES 
(3, 'branchEmployee', 1500, 1, NULL, '123456'),
(4, 'branchEmployee', 1600, 1, NULL, '123456'),
(5, 'branchEmployee', 1550, 1, NULL, '123456');


INSERT INTO Person (person_id, person_name, phone_num, address)
VALUES 
(11, 'Ali', 0591234567, 'Ramallah'),
(12, 'Mousa', 0591234567, 'Ramallah'),
(13, 'Salma', 0591234567, 'Ramallah');


INSERT INTO Employee (person_id, category, salary, branch_id, warehouse_id, password)
VALUES 
(11, 'branchEmployee', 1500, 2, NULL, '123456'),
(12, 'branchEmployee', 1600, 2, NULL, '123456'),
(13, 'branchEmployee', 1550, 2, NULL, '123456');



-- Warehouse Employees (will get IDs 4,5 as WE4, WE5)
INSERT INTO Employee (person_id, category, salary, branch_id, warehouse_id, password)
VALUES 
(6, 'warehouseEmployee', 1700, NULL, 'WH01', '123456'),
(7, 'warehouseEmployee', 1650, NULL, 'WH01', '123456');



INSERT INTO Customer (person_id, password)
VALUES 
(8, '123456');  -- Will get ID = 1, display as C1



INSERT INTO supplier (supplier_id, supplier_name, phone_num, address, email)
VALUES 
('s001', 'spices Supplier',059585959,'Ramallah','spice@1234'); 



INSERT INTO supplier (supplier_id, supplier_name, phone_num, address, email)
VALUES 
('s002', 'Oiles Supplier',059585959,'Ramallah','soile@1234'); 



INSERT INTO supplier (supplier_id, supplier_name, phone_num, address, email)
VALUES 
('s003', 'Frute Supplier',059585959,'Ramallah','frute@1234'); 






INSERT INTO Product (
    product_id,
    product_name,
    product_status,
    imported_quantity,
    available_quantity,
    reOrder_level,
    price,
    production_date,
    expired_date,
    product_category,
    product_discretion,
    product_unit
    
) VALUES 
('p11', 'Dried Cranberry', 'available', 100, 50, 10, 12.00, '2025-01-01', '2026-01-01', 
 'فواكه مجففة | Dried Fruits', 'High quality dried cranberries', 'GRAM'),
 
('p12', 'Dried Apricot', 'available', 80, 40, 8, 15.00, '2025-01-01', '2026-01-01', 
 'فواكه مجففة | Dried Fruits', 'Sweet dried apricots', 'GRAM'),
 
('p13', 'Olive Oil', 'available', 60, 30, 5, 45.00, '2025-01-01', '2026-12-01', 
 'زيوت | Oils', 'Extra virgin olive oil', 'Liter'),
 
('p14', 'Dried Pineapple', 'available', 50, 25, 5, 14.00, '2025-01-01', '2026-01-01', 
 'فواكه مجففة | Dried Fruits', 'Tropical dried pineapple', 'GRAM'),
 
('p15', 'Barbica Spice', 'available', 100, 60, 10, 8.00, '2025-01-01', '2026-06-01', 
 'بهارات | Spices', 'Traditional BBQ spice mix', 'GRAM'),
 
('p16', 'Cumin Powder', 'available', 80, 45, 8, 6.00, '2025-01-01', '2026-06-01', 
 'بهارات | Spices', 'Ground cumin spice', 'GRAM'),
 
('p17', 'Maqlubeh Spice', 'available', 70, 35, 7, 8.00, '2025-01-01', '2026-06-01', 
 'بهارات | Spices', 'Special maqlubeh seasoning', 'GRAM'),
 
('p18', 'Sesame Oil', 'available', 40, 20, 5, 35.00, '2025-01-01', '2026-12-01', 
 'زيوت | Oils', 'Pure sesame oil', 'Liter');




INSERT INTO warehouse_Product (warehouse_id, product_id, available_quantity) VALUES
('WH01', 'p11', 50),
('WH01', 'p12', 40),
('WH01', 'p13', 30),
('WH01', 'p14', 25),
('WH01', 'p15', 60),
('WH01', 'p16', 45),
('WH01', 'p17', 35),
('WH01', 'p18', 20);




INSERT INTO branch_Product (branch_id, product_id, available_quantity) VALUES
(1, 'p11', 30),
(1, 'p12', 25),
(1, 'p13', 15),
(1, 'p14', 20),
(1, 'p15', 40),
(1, 'p16', 30),
(1, 'p17', 25),
(1, 'p18', 12);





INSERT INTO branch_Product (branch_id, product_id, available_quantity) VALUES
(2, 'p11', 30),
(2, 'p12', 25),
(2, 'p13', 15),
(2, 'p14', 20),
(2, 'p15', 40),
(2, 'p16', 30),
(2, 'p17', 25),
(2, 'p18', 12);





select * from branch;
select * from warehouse;
select * from customer;
select * from employee;
select * from manager;
select * from person;
select * from product;
select * from branch_product;
select * from warehouse_product;

select * from sales_invoice;
