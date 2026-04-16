import mysql.connector

db = mysql.connector.connect(
   host="localhost",
    user="root",
    password="abeer@122S",
    database="salehkalaf"
)

cursor = db.cursor()
print("Connected")