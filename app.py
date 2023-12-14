from flask import Flask, render_template, session, redirect, request
import pymongo
import datetime
import os.path
from bson import ObjectId
import re
import string
import time, datetime
import random

my_client = pymongo.MongoClient("mongodb://localhost:27017/")
my_db = my_client["CityExpressMart"]
app = Flask(__name__)
app.secret_key = "cxpm"
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

admin_data = my_db["admin"]
product_category_data = my_db["product category"]
product_data = my_db["product"]
customer_data = my_db["customer"]
xpress_delivery_data = my_db["express_delivery"]
order_data = my_db["order"]
payment_collection = my_db["payment"]
store_data = my_db['grocery_store']

@app.route("/")
def index():
    message = request.args.get('message')
    if "role" in session and session["role"] == "Admin":
        session["login_count"] = 0
        return redirect("/admin-home")
    elif "role" in session and session["role"] == "Delivery":
        session["login_count"] = 0
        return redirect("/delivery-home")
    elif "role" in session and session["role"] == "Customer":
        session["login_count"] = 0
        return redirect("/customer-home")
    products = product_data.find()
    message = request.args.get('message')
    if message:
        return render_template("index.html", products=products, getStoreNameById=getStoreNameById, getCategoryNameById=getCategoryNameById, message=message, is_product_in_cart=is_product_in_cart)
    return render_template("index.html", products=products, getStoreNameById=getStoreNameById, getCategoryNameById=getCategoryNameById, is_product_in_cart=is_product_in_cart)


@app.route('/view-stores')
def store():
    stores = store_data.find()
    if 'role' in session and session['role'] == 'Customer':
        primary_store = session['primary_store']
        print(primary_store)
        return render_template('stores.html', stores=list(stores), primary_store = primary_store)
    return render_template('stores.html', stores=list(stores))
    
    

@app.route('/login')
def login():
    message = request.args.get('message')
    # return render_template('login.html')
    if message:
        return render_template('login.html', message=message)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/?message=Logout Successful!')

@app.route('/sign-up')
def signup():
    return render_template('sign-up.html')

@app.route('/admin-login')
def admin_login():
    return render_template('admin-login.html')

@app.route('/delivery-login')
def delivery_login():
    return render_template('delivery-login.html')

@app.route("/login-verify", methods=["post"])
def login_verify():
    role = request.form.get("role")
    username = request.form.get("email")
    password = request.form.get("password")
    if role == "Admin":
        query = {"email": username, "password": password}
        if admin_data.count_documents({}) == 0:
            admin_data.insert_one(
                {"email": "admin@xpress.com", "password": "admin"}
            )
        admin = admin_data.find_one(query)
        print(admin_data.count_documents(query))
        if admin is not None:
            session["admin_id"] = str(admin["_id"])
            session["role"] = "Admin"
            session["login_count"] = 1
            return redirect("/admin-home")
        return render_template(
            "admin-login.html",
            username=username,
            message="Invalid username or password, please try again!",
        )
    elif role == "Delivery":
        query = {"email": username, "password": password}
        delivery = xpress_delivery_data.find_one(query)
        if delivery is not None:
            session["role"] = "Delivery"
            session["delivery_id"] = str(delivery["_id"])
            session["login_count"] = 1
            return redirect("/delivery-home")
        return render_template(
            "delivery-login.html",
            username=username,
            message="Invalid username or password, please try again!",
        )
    elif role == "Customer":
        query = {"email": username, "password": password}
        customer = customer_data.find_one(query)
        if customer is not None:
            session["role"] = "Customer"
            session["customer_id"] = str(customer["_id"])
            session["login_count"] = 1
            session['primary_store'] = str(customer['primary_store'])
            return redirect("/customer-home")
        return render_template(
            "login.html",
            username=username,
            message="Invalid username or password, please try again!",
        )
    elif role == "NewCustomer":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        password = request.form.get('password')
        countEmail = customer_data.count_documents({"email": email})
        countPhone = customer_data.count_documents({"phone": phone})
        if countEmail == 0 and countPhone == 0:
            customer_data.insert_one(
                {
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "password": password,
                    "address": address,
                    "primary_store": ObjectId('6566de1fae31fb0590dac18d')
                }
            )
            return render_template(
                "login.html",
                username=email,
                message="account created successfully! you can login now!",
            )
        return render_template(
            "sign-up.html",
            message="User already exist with given email or phone! Try with different one",
            name=name,
            phone=phone,
            email=email,
            address=address,
        )
    return render_template("login.html")

@app.route("/admin-home")
def admin_home():
    return render_template("admin-home.html")

@app.route("/delivery-home")
def delivery_home():
    return render_template("delivery-home.html")

@app.route("/customer-home")
def customer_home():
    products = product_data.find()
    message = request.args.get('message')
    stores = store_data.find({})
    customer_id = session['customer_id']
    customer = customer_data.find_one({'_id':ObjectId(customer_id)})
    store_id = customer['primary_store']
    if store_id:
        products = product_data.find({'store_id': ObjectId(store_id)})
        return render_template("customer-home.html", products=products, getStoreNameById=getStoreNameById, getCategoryNameById=getCategoryNameById, is_product_in_cart=is_product_in_cart, primary_store=str(store_id), stores = list(stores))
    if message:
        return render_template("customer-home.html", products=products, getStoreNameById=getStoreNameById, getCategoryNameById=getCategoryNameById, message=message, is_product_in_cart=is_product_in_cart,primary_store=store_id, stores = list(stores))
    return render_template("customer-home.html", products=products, getStoreNameById=getStoreNameById, getCategoryNameById=getCategoryNameById, is_product_in_cart=is_product_in_cart,primary_store=str(store_id), stores = list(stores))


@app.route('/category')
def category():
    categories = product_category_data.find()
    return render_template('add-category.html', categories=categories)

@app.route('/add-category', methods=['POST'])
def add_category():
    name = request.form.get('name')
    if product_category_data.count_documents({'name':name}) == 0:
        product_category_data.insert_one({'name': name})
        return redirect('/category?message=Category Added!')
    return redirect('/category?message=Category Already Exists!')


@app.route("/admin-orders")
def admin_orders():
    orders = order_data.find({"status": {"$ne": "cart"}})
    deliveryTeam = xpress_delivery_data.find()
    message = request.args.get("message")

    filterValue = request.args.get("filterStatus")
    if filterValue:
        orders = order_data.find({"status": filterValue})
    if not filterValue:
        filterValue = "all"
    return render_template(
        "admin-orders.html",
        orders=orders,
        agents=deliveryTeam,
        get_product_by_product_id=get_product_by_product_id,
        getStoreNameById=getStoreNameById,
        filterValue=filterValue,
        message=message,
        getUpperIdFromOrderId=getUpperIdFromOrderId
    )

@app.route("/admin-order")
def admin_order():
    order_id = request.args.get("order_id")
    action = request.args.get("action")
    order = order_data.find_one({'_id': ObjectId(order_id)})
    if order['delivery_type'] == 'Delivery':
        if action == 'accepted':
            order_data.update_one({'_id':ObjectId(order_id)}, {'$set': {'status': 'accepted'}})
        elif action == 'rejected':
            order_data.update_one({'_id': ObjectId(order_id)}, {'$set': {'status': 'rejected', 'refund_status': 'processing'}})
        elif action == 'prepared':
            order_data.update_one({'_id':ObjectId(order_id)}, {'$set': {'status': 'prepared'}})
        elif action == 'assigned':
            delivery_id = request.args.get('delivery_id')
            order_data.update_one({'_id':ObjectId(order_id)}, {'$set': {'status': 'assigned', 'delivery_id': ObjectId(delivery_id)}})
        elif action == 'process_refund':
            order_data.update_one({'_id':ObjectId(order_id)}, {'$set': {'status': 'refund processed'}})
    if order['delivery_type'] == 'Pickup':
        if action == 'accepted':
            order_data.update_one({'_id':ObjectId(order_id)}, {'$set': {'status': 'accepted'}})
        elif action == 'rejected':
            order_data.update_one({'_id': ObjectId(order_id)}, {'$set': {'status': 'rejected', 'refund_status': 'processing'}})
        elif action == 'prepared':
            order_data.update_one({'_id':ObjectId(order_id)}, {'$set': {'status': 'prepared'}})
        elif action == 'picked':
            order_data.update_one({'_id':ObjectId(order_id)}, {'$set': {'status': 'Picked Up'}})
        elif action == 'process_refund':
            order_data.update_one({'_id':ObjectId(order_id)}, {'$set': {'status': 'refund processed'}})

    
    return redirect('/admin-orders')
    
@app.route('/set-new-password',  methods=['post'])
def set_new_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    if 'role' in session and session['role'] == 'Customer':
        customer = customer_data.find_one({'_id': ObjectId(session['customer_id'])})
        current_password = customer['password']
        if old_password == current_password:
            if new_password == confirm_password:
                customer_data.update_one({'_id': customer['_id']}, {'$set':{'password': new_password}})
                return redirect('/?message=password changed successfully')
            return redirect('/?message=New and Confirm Password are not same')
        return redirect('/?message=Entered wrong password')
    elif 'role' in session and session['role'] == 'Delivery':
        delivery = xpress_delivery_data.find_one({'_id': ObjectId(session['delivery_id'])})
        current_password = delivery['password']
        if old_password == current_password:
            if new_password == confirm_password:
                xpress_delivery_data.update_one({'_id': delivery['_id']}, {'$set':{'password': new_password}})
                return redirect('/?message=password changed successfully')
            return redirect('/change-password?message=New and Confirm Password are not same')
        return redirect('/change-password?message=Entered wrong password')
    
            
@app.route('/change-password')
def change_password():
    message = request.args.get('message')
    return render_template('change-password.html', message=message)


@app.route("/delivery-orders")
def delivery_orders():
    filterType = request.args.get("status")
    print(filterType)
    print({"delivery_assigned": ObjectId(session["delivery_id"])})
    orders = order_data.find(
        {"delivery_id": ObjectId(session["delivery_id"])}
    )
    if filterType:
        query = {
            "delivery_id": ObjectId(session["delivery_id"]),
            "status": filterType,
        }
        orders = order_data.find(
           query
        )
    return render_template(
        "delivery-orders.html",
        orders=orders,
        get_product_by_product_id=get_product_by_product_id,
        getUpperIdFromOrderId=getUpperIdFromOrderId
    )


@app.route('/delivery-order')
def delivery_order():
    order_id = request.args.get('order_id')
    action = request.args.get('action')
    delivery_id = ObjectId(session['delivery_id'])
    if action == 'picked_package':
        order_data.update_one({'_id': ObjectId(order_id), 'delivery_id': delivery_id}, {'$set': {'status': 'out for delivery'}})
    if action == 'delivered':
        order_data.update_one({'_id': ObjectId(order_id), 'delivery_id': delivery_id}, {'$set': {'status': 'delivered'}})
    return redirect('/delivery-orders')



@app.route('/delivery')
def delivery():
    message = request.args.get('message')
    delivery_agents = xpress_delivery_data.find()
    return render_template('add-delivery-agent.html', delivery_agents=delivery_agents, message=message)

@app.route('/add-delivery', methods=['POST'])
def add_delivery():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    password = request.form.get('password')
    count = xpress_delivery_data.count_documents({'email': email})
    if count == 0:
        xpress_delivery_data.insert_one({'email': email, 'name':name, 'phone':phone,'address': address, 'password':password})
        return redirect('/delivery?message=agent added successfully!')
    return redirect('/delivery?message=username already exists!')

@app.route("/add-product", methods=["POST"])
def add_product():
    category_id = request.form.get("category_id")
    brand = request.form.get("brand")
    price = request.form.get("price")
    name = request.form.get("name")
    stock = request.form.get("quantity")
    picture = request.files.get("picture")
    path = APP_ROOT + "/static/img/" + picture.filename
    description = request.form.get("description")
    picture.save(path)
    store_id = request.form.get('store_id')
    query = {"name": name}
    count = product_data.count_documents(query)
    if count == 0:
        query = {
            "name": name,
            "brand": brand,
            "picture": picture.filename,
            "price": price,
            "category_id": ObjectId(category_id),
            "store_id": ObjectId(store_id),
            "quantity": stock,
            "description": description,
        }
        product_data.insert_one(query)
        return redirect("/add-view-products?message=added")
    else:
        redirect("/add-view-products?message=duplicateproduct")

@app.route("/add-view-products")
def add_products():
    message = request.args.get("message")
    if message == "created":
        message = "Product Created Successfully"
    if message == "duplicateproduct":
        message = "product already exists!"
    products = product_data.find()
    product_count = product_data.count_documents({})
    stores = store_data.find({})
    if product_category_data.count_documents({}) == 0:
        message = "No categories added! Add category before adding a product"
    categories = product_category_data.find()
    
    return render_template(
        "add-product.html",
        products=products,
        product_count=product_count,
        categories=list(categories),
        stores=stores,
        message=message,
        getCategoryNameById=getCategoryNameById,
        getStoreNameById=getStoreNameById
    )

@app.route("/add-to-cart")
def add_to_cart():
    if "role" not in session:
        return redirect(
            "/login?message=Sign in or Sign up to get started with shopping cart"
        )
    if session["role"] == "Customer":
        quantity = request.args.get("qty")
        product_id = request.args.get("product_id")
        product = product_data.find_one({'_id': ObjectId(product_id)})
        product_name = product['name']
        customer_id = session["customer_id"]
        customer = customer_data.find({'_id': ObjectId(customer_id)})

        message=""
        query = {"customer_id": ObjectId(customer_id), "status": "cart"}
        count = order_data.count_documents(query)
        if count > 0:
            order = order_data.find_one(query)
            order_id = order["_id"]
            count = order_data.count_documents(
                {
                    "_id": ObjectId(order_id),
                    "status": "cart",
                    "items.product_id": ObjectId(product_id),
                }
            )
            if count > 0:
                order_data.update_one(
                    {
                        "_id": ObjectId(order_id),
                        "status": "cart",
                        "items.product_id": ObjectId(product_id),
                    },
                    {"$set": {"items.$.quantity": quantity}},
                )
            else:
                order_data.update_one(
                    {
                        "_id": ObjectId(order_id),
                        "status": "cart",
                    },
                    {
                        "$push": {
                            "items": {
                                "quantity": quantity,
                                "product_id": ObjectId(product_id),
                                'store_id': product['store_id']
                            },
                        }
                    },
                )
        else:
            product_to_cart = {"product_id": ObjectId(product_id), "quantity": 1, 'store_id':product['store_id']}
            query = {
                "customer_id": ObjectId(customer_id),
                "status": "cart",
                "items": [product_to_cart],
            }
            order_data.insert_one(query)
        operation = request.args.get('operation')
        if operation and operation == 'qty':
                return redirect("/cart")
        return redirect("/customer-home?message="+product_name+" Added to cart")

@app.route("/cart")
def cart():
    if "role" not in session:
        return render_template(
            "login.html",
            message="Login to your Account",
        )
    stores = store_data.find()
    delivery_type = request.args.get('del_type')
    if not delivery_type:
        delivery_type = "Delivery"
    if session["role"] == "Customer":
        order = order_data.find_one(
            {"customer_id": ObjectId(session["customer_id"]), "status": "cart"}
        )
        count = order_data.count_documents(
            {"customer_id": ObjectId(session["customer_id"]), "status": "cart"}
        )
        if count > 0:
            subtotal = 0
            total = 0
            total_quantity_items = 0
            query = {
                "customer_id": ObjectId(session["customer_id"]),
                "status": "cart",
                "items": {"$exists": True, "$size": 0},
            }
            # Execute the query
            empty_items_order = order_data.find_one(query)
            if empty_items_order is None:
                products_in_cart = order.get("items", [])
                for product_in_cart in products_in_cart:
                    product = get_product_by_product_id(product_in_cart["product_id"])
                    price = product["price"]
                    subtotal += int(price) * int(product_in_cart["quantity"])
                    total_quantity_items = total_quantity_items + int(product_in_cart["quantity"])
                    total = subtotal * 1.08
                    
                    delivery_fee = 5
                    if subtotal > 49:
                        delivery_fee = 0
                    if delivery_type == 'Delivery':
                        total = total + delivery_fee
                return render_template(
                    "cart.html",
                    order=order,
                    products_in_cart=products_in_cart,
                    get_product_by_product_id=get_product_by_product_id,
                    total="{:.2f}".format(total * 1.08),
                    subtotal=subtotal,
                    delivery_type = delivery_type,
                    tax="{:.2f}".format(subtotal * 0.08),
                    delivery_fee = delivery_fee,
                    stores=list(stores),
                    primary_store = session['primary_store']
                )
        return redirect("/customer-home?message=No items in cart")

@app.route("/remove")
def remove():
    product_id = request.args.get("product_id")
    order_id = request.args.get("order_id")
    # Remove the specific item from the items array
    query = {
        "_id": ObjectId(order_id),
        "status": "cart",
        "items.product_id": ObjectId(product_id),
    }
    update_operation = {"$pull": {"items": {"product_id": ObjectId(product_id)}}}
    order_data.update_one(query, update_operation)
    order = order_data.find_one({"_id": ObjectId(order_id)})
    query = {"_id": ObjectId(order_id), "items": {"$exists": True, "$size": 0}}
    # Execute the query
    empty_items_order = order_data.find_one(query)
    if empty_items_order is not None:
        order_data.delete_one({"_id": ObjectId(order_id)})
        return redirect("/customer-home?message=Cart is empty, Shop to add to cart")
    return redirect("/cart")


def is_product_in_cart(product_id):
    if 'role' not in session:
        return False
    customer_id = session['customer_id']
    query_to_cart_status = {'status':'cart', 'customer_id': ObjectId(customer_id)}
    count_status_cart = order_data.count_documents(query_to_cart_status)
    if count_status_cart > 0:
        order = order_data.find_one(query_to_cart_status)
        order_id = order['_id']
        count_in_cart = order_data.count_documents(
                {
                    "_id": ObjectId(order_id),
                    "status": "cart",
                    "items.product_id": ObjectId(product_id),
                }
            )
        if count_in_cart > 0:
            return True
    return False


@app.route("/payment-gateway")
def payment_gateway():
    order_id = request.args.get("order_id")
    amount = request.args.get("amount")
    del_type = request.args.get('del_type')
    pickup_location = request.args.get('pickup_location')
    subtotal = request.args.get('subtotal')
    return render_template("payment.html", order_id=order_id, amount=amount, pickup_location=pickup_location, del_type=del_type, subtotal=subtotal)

@app.route("/payment-verification", methods=["post"])
def payment_verification():
    delivery_type = request.form.get("delivery_type")
    order_id = request.form.get("order_id")
    amount = request.form.get("amount")
    customer_id = ObjectId(session["customer_id"])
    card_type = request.form.get("card_type")
    name = request.form.get("card_name")
    number = request.form.get("card_number")
    payment_type = request.form.get("payment_type")
    expiry = request.form.get("expiry")
    cvv = request.form.get("cvv")
    pickup_location = request.form.get('pickup_location')
    address = request.form.get('address')
    subtotal = request.form.get('subtotal')
    order_details = {}
    payment_details = {
            "order_id": ObjectId(order_id),
            "amount": amount,
            "customer_id": customer_id,
            "card_type": card_type,
            "card_holder": name,
            "card_id": number,
            "payment_type": payment_type,
            "expiry_date": expiry, 
            "cvv": cvv,
            "payment_date": datetime.datetime.now().strftime("%m-%d-%Y")
        }
    payment_collection.insert_one(payment_details)
    if delivery_type and delivery_type == 'Delivery':
        delivery_fee = 5
        if subtotal and subtotal.isdigit() and int(subtotal) > 49:
            delivery_fee: 0
        order_details = {
            "status": "pending",
            "amount": amount,
            "delivery_type": delivery_type,
            'delivery_address': address,
            'delivery_fee': delivery_fee,
            'order_date': datetime.datetime.now().strftime("%m-%d-%Y")
        }
    else:
        order_details = {
            "status": "pending",
            "amount": amount,
            "delivery_type": delivery_type,
            'pickup_location': ObjectId(pickup_location),
            'order_date': datetime.datetime.now().strftime("%m-%d-%Y")
        }

    order_data.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": order_details
        },
    )
    return redirect("/customer-orders?message=order placed successful")


@app.route('/remove-product')
def remove_product():
    product_id = request.args.get('product_id')
    product_data.delete_one({'_id': ObjectId(product_id)})
    message = "product deleted successfully"
    return redirect('/add-view-products?message'+message)

@app.route('/remove-delivery-agent')
def remove_delivery_agent():
    delivery_id = request.args.get('delivery_id')
    xpress_delivery_data.delete_one({'_id': ObjectId(delivery_id)})
    message = "delivery agent deleted successfully"
    return redirect('/delivery?message'+message)

@app.route("/customer-orders")
def customer_orders():
    message = request.args.get("message")
    if "role" not in session:
        return render_template(
            "login.html",
            message="No Orders So Far",
        )
    if session["role"] == "Customer":
        orders = order_data.find(
            {"customer_id": ObjectId(session["customer_id"]), "status": {"$ne": "cart"}}
        )
        count = order_data.count_documents(
            {"customer_id": ObjectId(session["customer_id"]), "status": {"$ne": "cart"}}
        )
        primary_store = session['primary_store']
        print( 'customer-orders ',primary_store)
        stores = store_data.find()
        return render_template(
                "customer-orders.html",
                orders=orders,
                orders_count = count,
                get_product_by_product_id=get_product_by_product_id,
                getUpperIdFromOrderId=getUpperIdFromOrderId,
                getStoreNameById = getStoreNameById,
                message=request.args.get("message"),
                stores=list(stores),
                primary_store = primary_store
            )
    return render_template("customer-orders.html", message=message)
#  To insert dummy store
@app.route('/add-store', methods=['POST'])
def add_store():
    name = request.form.get('name')
    street = request.form.get('street')
    location = request.form.get('location')
    zipcode = request.form.get('zip_code')
    store_data.insert_one({'name': name, 'location': location, 'street': street, 'zip_code': zipcode})
    stores = store_data.find({})
    return render_template('stores.html', stores=stores)

@app.route('/update-product')
def update_product():
    product_id = request.args.get('product_id')
    quantity = request.args.get('qty')
    product_data.update_one({'_id': ObjectId(product_id)}, {'$set':{'quantity': quantity}})
    products = product_data.find()
    product_count = product_data.count_documents({})
    stores = store_data.find({})
    if product_category_data.count_documents({}) == 0:
        message = "No categories added! Add category before adding a product"
    categories = product_category_data.find()
    message='product quantity updated'
    return render_template(
        "add-product.html",
        products=products,
        product_count=product_count,
        categories=list(categories),
        stores=stores,
        message=message,
        getCategoryNameById=getCategoryNameById,
        getStoreNameById=getStoreNameById
    )

@app.route('/update-default-store')
def update_store_default():
    store_id = request.args.get('primary_store')
    if 'role' in session and session['role'] == 'Customer':
        customer_id = session['customer_id']
        session['primary_store'] = store_id
        customer_data.update_one({'_id': ObjectId(customer_id)}, {'$set': {'primary_store': ObjectId(store_id)}})
        store = store_data.find_one({'_id': ObjectId(store_id)})
        return redirect('/?message='+ store['name'] +' default store ')
    return redirect('/')

def getCategoryNameById(category_id):
    category = product_category_data.find_one({'_id': ObjectId(category_id)})
    return category['name']

def getStoreNameById(store_id):
    store = store_data.find_one({'_id': store_id})
    return store['location']

def get_product_by_product_id(product_id):
    query = {"_id": product_id}
    product = product_data.find_one(query)
    return product

def getUpperIdFromOrderId(order_id):
    stri = str(order_id)
    substr = stri[-6:].upper()
    return substr

@app.route('/make_primary_store')
def makePrimaryStoreForCustomers():
    customer_data.update_one({'_id': ObjectId('656e21af4f710768ab76406c')}, {'$set': {'primary_store': ObjectId('6566de1fae31fb0590dac18d')}})
    return 'success'


app.run(debug=True, port=5003)