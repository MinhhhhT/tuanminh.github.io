import mysql.connector

# Kết nối đến csdl qlsv
mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='01216335242m',
    database='qldh',
    autocommit=True
)

# Tạo đối tượng cursor() để thao tác với csdl qlsv
cursor = mydb.cursor()
