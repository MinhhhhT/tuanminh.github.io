from decimal import Decimal
from flask import Flask, render_template, request, redirect
from db_config import mydb, cursor

app = Flask(__name__)

# Trang danh sách đơn hàng
@app.route('/')
def index():
    # Lấy các dữ liệu của đơn hàng và hiển thị ra màn hình
    cursor.execute('''SELECT orders.orderID, customers.customerName, products.productName, orders.orderDate, orderdetails.quantity, orders.totalAmount, products.imagePath
                            FROM customers
                            JOIN orders ON customers.customerID = orders.customerID
                            JOIN orderdetails ON orders.orderID = orderdetails.orderID
                            JOIN products ON orderdetails.productID = products.productID
                        ''')
    # Lưu toàn bộ bản ghi lấy ra được lưu vào orders
    orders = cursor.fetchall()
    return render_template('index.html', orders=orders)

# Trang danh sách sản phẩm
@app.route('/home')
def home():
    # Lấy dữ liệu của bảng products
    cursor.execute('SELECT * FROM qldh.products')
    # Lưu toàn bộ bản ghi vào biến products
    products = cursor.fetchall()
    return render_template('home.html', products=products)

# Thêm sản phẩm
@app.route('/add/<int:id>', methods=['GET', 'POST'])
def add(id):
    # Lấy dữ liệu sản phẩm từ bảng products với điều kiện là productID = id của sản phẩm được click
    cursor.execute(f'SELECT * FROM qldh.products WHERE productID = {id}')
    # Lưu duy nhất một bản ghi vào trong biến product
    product = cursor.fetchone()
    # Kiểm tra nếu dữ liệu được gửi lên thì lấy những dữ liệu đó lưu vào các biến
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        product_name = request.form.get('product_name')
        product_price = Decimal(request.form.get('price')).quantize(Decimal('0.000'))  # Hàm quantize định dạng số decimal là số có 3 số sau dấu phẩy
        quantity = int(request.form.get('quantity'))
        total_amount = product_price * quantity
        # Kiểm tra dữ liệu nhập vào có đầy đủ hay không
        if customer_name and product_name and quantity: 
            # Bắt đầu transacation    
            mydb.start_transaction()
            # Thêm dữ liệu vào bảng customers
            sql = f'INSERT INTO qldh.customers (customerName) VALUES("{customer_name}")'
            cursor.execute(sql)
            
            # Thêm dữ liệu vào bảng orders
            sql = f'INSERT INTO qldh.orders (orderDate, customerID, totalAmount) VALUES(CURDATE(), LAST_INSERT_ID(), {total_amount})'
            cursor.execute(sql)

            # Thêm dữ liệu vào bảng orderDetails
            sql = f'INSERT INTO qldh.orderdetails (orderID, productID, quantity, price) VALUES(LAST_INSERT_ID(), {id}, {quantity}, {total_amount})'
            cursor.execute(sql)
            
            # Kết thúc transcation và lưu dữ liệu
            mydb.commit()
            # Quay lại trang / (tức trang đơn hàng)
            return redirect('/')
        else : 
            # Hiển thị lỗi nếu các ô trống không được nhập đầy đủ, thiếu dữ liệu đầu vào
            error_message = 'Vui lòng nhập đầy đủ thông tin'
            return render_template('add.html', product=product, error_message=error_message)
    return render_template('add.html', product=product)

# Hàm tìm kiếm đơn hàng theo tên khách hàng hoặc mã đơn hàng hoặc tên sản phẩm
@app.route('/search/orders')
def search_orders():
    # Láy dữ liệu nhập vào từ ô input có name là search_query lưu vào biến search_query
    search_query = request.args.get('search_query', '')
    # Lấy ra dữ liệu trong các bảng dữ liệu theo tên khách hàng, mã đơn hàng, tên sản phẩm bằng với từ khóa search_query
    sql = f'''SELECT orders.orderID, customers.customerName, products.productName, orders.orderDate, orderdetails.quantity, orders.totalAmount, products.imagePath
                            FROM customers
                            JOIN orders ON customers.customerID = orders.customerID
                            JOIN orderdetails ON orders.orderID = orderdetails.orderID
                            JOIN products ON orderdetails.productID = products.productID
                            WHERE customers.customerName LIKE '%{search_query}%' OR orders.orderID LIKE '%{search_query}%' OR products.productName LIKE '%{search_query}%' '''
    cursor.execute(sql)
    orders = cursor.fetchall()
    return render_template('index.html', orders=orders)

# Tìm kiếm sản phẩm theo tên sản phẩm
@app.route('/search/products')
def search_products():
    # Lấy dữ liệu từ ô input có name là search_query
    search_query = request.args.get('search_query', '')
    # Tìm kiếm tên sản phẩm hoặc mã sản phẩm theo từ khóa search_query
    sql = f'''SELECT productID, productName, description, price, imagePath
            FROM products
            WHERE productName LIKE '%{search_query}%' OR productID = '%{search_query}% '''
    cursor.execute(sql)
    products = cursor.fetchall()
    return render_template('home.html', products=products)

# Cập nhật dữ liệu theo id của đơn hàng
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    # Lấy dữ liệu đơn hàng theo điều kiện orderID là id của sản phẩm được click vào
    cursor.execute(f'''SELECT orders.orderID, customers.customerName, products.productName, orderdetails.quantity, products.price
                            FROM customers
                            JOIN orders ON customers.customerID = orders.customerID
                            JOIN orderdetails ON orders.orderID = orderdetails.orderID
                            JOIN products ON orderdetails.productID = products.productID
                            WHERE orders.orderID = {id}
                        ''')
    # Lưu duy nhất một bản ghi vào biến order
    order = cursor.fetchone()
    # Kiểm tra nếu dữ liệu được gửi lên thì lấy những dữ liệu đó lưu vào các biến
    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        quantity = int(request.form.get('quantity'))
        price = Decimal(order[4])   # Lấy ra giá trị của phần tử thứ 5 trong list order, sau đó chuyển đổi sang kiểu dữ liệu decimal rồi lưu vào biến price
        total_amount = quantity * price  
        # Kiểm tra các dữ liệu được nhập vào đã đầy đủ chưa
        if customer_name and quantity: 
            # Cập nhật dữ liệu với điều kiện orderID = id
            sql = f'''UPDATE orders
                    JOIN customers ON customers.customerID = orders.customerID
                    JOIN orderdetails ON orders.orderID = orderdetails.orderID
                    JOIN products ON orderdetails.productID = products.productID
                    SET customers.customerName = "{customer_name}", orderdetails.quantity = {quantity}, orders.totalAmount = {total_amount}
                    WHERE orders.orderID = {id};
                    '''
            cursor.execute(sql)
            mydb.commit()
            return redirect('/')
        else : 
            # Hiển thị ra lỗi khi dữ liệu không đủ
            error_message = 'Vui lòng nhập đầy đủ thông tin'
            return render_template('edit.html', error_message=error_message)
    return render_template('edit.html', order=order)

# Xóa đơn hàng theo id của đơn hàng
@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    # Xóa bảng orderdetails
    sql = f"DELETE FROM orderdetails WHERE orderID = {id}"
    cursor.execute(sql)
    
    # Xóa bảng orders
    sql = f"DELETE FROM orders WHERE orderID = {id}"
    cursor.execute(sql)

    # Lưu lại thay đổi
    mydb.commit()
    return redirect('/')   
        
if __name__ == '__main__':
    app.run(debug=True)
    
    
    
