from datetime import datetime, timedelta
from functools import wraps
import hashlib
import os
import re
from flask import Flask, jsonify, redirect, url_for, render_template, request
from pymongo import MongoClient
import jwt
from dotenv import load_dotenv
from os.path import join, dirname
from babel.numbers import format_currency
from babel.dates import format_date, format_datetime, format_time
import locale
from uuid import uuid4
from imagekitio import ImageKit
from werkzeug.utils import secure_filename


dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)
locale.setlocale(locale.LC_ALL, "id_ID.UTF-8")
UPLOAD_FOLDER = './static/uploads'

SECRET_KEY = "KEDAIIMAJI"
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

PUBLIC_KEY_TOKEN_IMAGEKIT = os.environ.get("PUBLIC_KEY_TOKEN_IMAGEKIT")
PRIVATE_KEY_TOKEN_IMAGEKIT =  os.environ.get("PRIVATE_KEY_TOKEN_IMAGEKIT")




MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

app.jinja_env.filters["format_currency"] = format_currency


@app.route("/", methods=["GET", "POST"])
def home():
    
    token_receive = request.cookies.get("mytoken")
    if token_receive:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
            if user_info['profile_image'] == None:
                user_info["profile_image"] = 'https://ik.imagekit.io/coffeeshopteam3/profile_placeholdesr.png'
            if not user_info:
                return redirect(url_for("login"))
            return render_template(
                "index.html", user_info=user_info
            )

        except jwt.ExpiredSignatureError:
            return
    return render_template("index.html")


@app.route("/about/", methods=["GET", "POST"])
def about():
    
    token_receive = request.cookies.get("mytoken")
    if token_receive:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
            if user_info['profile_image'] == None:
                user_info["profile_image"] = 'https://ik.imagekit.io/coffeeshopteam3/profile_placeholdesr.png'
            if not user_info:
                return redirect(url_for("login"))
            return render_template(
                "about.html", user_info=user_info
            )

        except jwt.ExpiredSignatureError:
            return
    return render_template("about.html")


@app.route("/contact/", methods=["GET", "POST"])
def contact():
    token_receive = request.cookies.get("mytoken")
    if token_receive:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
            if user_info['profile_image'] == None:
                user_info["profile_image"] = 'https://ik.imagekit.io/coffeeshopteam3/profile_placeholdesr.png'
            if not user_info:
                return redirect(url_for("login"))
            return render_template(
                "contact.html", user_info=user_info 
            )

        except jwt.ExpiredSignatureError:
            return
   

    return render_template("contact.html")


@app.route("/menu/", methods=["GET"])
def menu():
    category = request.args.get("category")
    if category:
        menus = list(db.menu.find({"kategori": category}, {"_id": False}))
    else:
        menus = list(db.menu.find({}, {"_id": False}))

    for item in menus:
        total_ratings = sum([item.get(f"rating_{i}", 0) * i for i in range(1, 6)])
        total_reviews = sum([item.get(f"rating_{i}", 0) for i in range(1, 6)])
        item["average_rating"] = (
            total_ratings / total_reviews if total_reviews > 0 else 0
        )
        
    token_receive = request.cookies.get("mytoken")
    if token_receive:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
            if user_info['profile_image'] == None:
                user_info["profile_image"] = 'https://ik.imagekit.io/coffeeshopteam3/profile_placeholdesr.png'
            if not user_info:
                return redirect(url_for("login"))
            return render_template(
                "menu.html", user_info=user_info,menus=menus
            )

        except jwt.ExpiredSignatureError:
            return
   
    return render_template("menu.html", menus=menus)


@app.route("/filter_menu", methods=["GET"])
def filter_menu():
    category = request.args.get("category")
    if category:
        menus = list(db.menu.find({"kategori": category}, {"_id": False}))
    else:
        menus = list(db.menu.find({}, {"_id": False}))

    for item in menus:
        total_ratings = sum([item.get(f"rating_{i}", 0) * i for i in range(1, 6)])
        total_reviews = sum([item.get(f"rating_{i}", 0) for i in range(1, 6)])
        item["average_rating"] = (
            total_ratings / total_reviews if total_reviews > 0 else 0
        )

    return jsonify(menus)


def get_menu_item(menu_id):
    return db.menu.find_one({"menuId": menu_id})


@app.route("/cart/", methods=["GET", "POST"])
def cart():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]})
        menu = db.menu.find({}, {"_id": False})
        menu = menu[:4]

        formatted_menu = []
        for item in menu:
            item["harga"] = locale.format_string(
                "Rp. %d", int(item["harga"]), grouping=True
            )
            formatted_menu.append(item)

        cart_items = user_info.get("cart", [])

        total_price = 0
        for item in cart_items:
            menu_item = get_menu_item(item["menuId"])
            item["image"] = menu_item["image"]
            item["name"] = menu_item["nama"]
            item["price"] = int(menu_item["harga"])
            item_total = item["price"] * item["quantity"]
            total_price += item_total

        discount = 0
        tax = int(total_price * 0.10)
        final_total_price = total_price - discount + tax

        formatted_cart_items = []
        for item in cart_items:
            item["formatted_price"] = locale.format_string(
                "Rp. %d", item["price"], grouping=True
            )
            item["formatted_total"] = locale.format_string(
                "Rp. %d", item["price"] * item["quantity"], grouping=True
            )
            if isinstance(item["option2"], list):
                item["option2"] = ", ".join(item["option2"])
            formatted_cart_items.append(item)

        return render_template(
            "cart.html",
            menu=formatted_menu,
            user_info=user_info,
            cart_items=formatted_cart_items,
            total_price=locale.format_string("Rp. %d", total_price, grouping=True),
            discount=locale.format_string("Rp. %d", discount, grouping=True),
            tax=locale.format_string("Rp. %d", tax, grouping=True),
            final_total_price=locale.format_string(
                "Rp. %d", final_total_price, grouping=True
            ),
        )
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="Your token has expired"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="There was a problem logging you in"))


@app.route("/update_quantity", methods=["POST"])
def update_quantity():
    data = request.get_json()
    menu_id = data.get("menu_id")
    new_quantity = data.get("quantity")

    token_receive = request.cookies.get("mytoken")
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
    user_info = db.users.find_one({"email": payload["id"]})

    for item in user_info["cart"]:
        if item["menuId"] == menu_id:
            item["quantity"] = new_quantity
            break

    db.users.update_one({"email": payload["id"]}, {"$set": {"cart": user_info["cart"]}})

    total_price = sum(
        int(get_menu_item(item["menuId"])["harga"]) * item["quantity"]
        for item in user_info["cart"]
    )
    discount = 0
    tax = int(total_price * 0.10)
    final_total_price = total_price - discount + tax

    updated_item_price = int(get_menu_item(menu_id)["harga"])
    updated_total = new_quantity * updated_item_price

    response_data = {
        "total_price": f"Rp. {total_price:,}".replace(",", "."),
        "discount": f"Rp. {discount:,}".replace(",", "."),
        "tax": f"Rp. {tax:,}".replace(",", "."),
        "final_total_price": f"Rp. {final_total_price:,}".replace(",", "."),
        "formatted_total": f"Rp. {updated_total:,}".replace(",", "."),
        "formatted_price": f"Rp. {updated_item_price:,}".replace(",", "."),
    }

    return jsonify(response_data)


@app.route("/profile/", methods=["GET", "POST"])
def profile():
    token_receive = request.cookies.get("mytoken")
    if not token_receive:
        return redirect(url_for("login"))

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
        if user_info['profile_image'] == None:
            user_info["profile_image"] = 'https://ik.imagekit.io/coffeeshopteam3/profile_placeholdesr.png'
        if not user_info:
            return redirect(url_for("login"))

        order_history = list(
            db.orders.find({"user_email": user_info["email"]}, {"_id": False})
        )
        
        for order in order_history:
            order["timestamp"] = order["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            for item in order["order_items"]:
                if isinstance(item["option2"], list):
                    item["option2"] = ", ".join(item["option2"])

        return render_template(
            "profile.html", user_info=user_info, order_history=order_history
        )

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/check_review", methods=["POST"])
def check_review():
    order_id = request.form.get("order_id")
    item_id = request.form.get("item_id")
    token_receive = request.cookies.get("mytoken")

    if not token_receive:
        return jsonify({"message": "Login required to check review"})

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})

        if not user_info:
            return jsonify({"message": "User not found"})

        existing_review = db.reviews.find_one(
            {
                "item_id": item_id,
                "user_email": user_info["email"],
                "order_id": int(order_id),
            }
        )
        
        if existing_review:
            return jsonify({"reviewed": True})
        else:
            return jsonify({"reviewed": False})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({"message": "Invalid token"})


@app.route("/submit_review", methods=["POST"])
def submit_review():
    token_receive = request.cookies.get("mytoken")

    if not token_receive:
        return jsonify({"message": "Login required to submit a review"})

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})

        if not user_info:
            return jsonify({"message": "User not found"})

        item_id = request.form.get("item_id")
        review_text = request.form.get("reviewText")
        rating = int(request.form.get("rating"))
        order_id = request.form.get("order_id")

        existing_review = db.reviews.find_one(
            {
                "item_id": item_id,
                "user_email": user_info["email"],
                "order_id": int(order_id),
            }
        )

        if existing_review:
            return jsonify(
                {"message": "You have already reviewed this item for this order"}
            )

        review_doc = {
            "item_id": item_id,
            "user_email": user_info["email"],
            "review_text": review_text,
            "rating": rating,
            "order_id": int(order_id),
            "timestamp": datetime.now(),
        }

        db.reviews.insert_one(review_doc)

        rating_field = f"rating_{rating}"
        db.menu.update_one({"menuId": item_id}, {"$inc": {rating_field: 1}})

        return redirect(url_for("profile"))

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({"message": "Invalid token"})


@app.route("/confirm_purchase", methods=["POST"])
def confirm_purchase():
    token_receive = request.cookies.get("mytoken")
    if not token_receive:
        return jsonify({"success": False, "message": "User not logged in"})

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_email = payload["id"]

        user = db.users.find_one({"email": user_email})
        cart_items = user.get("cart", [])

        total_price = 0
        for item in cart_items:
            menu_item = get_menu_item(item["menuId"])
            item["image"] = menu_item.get("image", "")
            item["name"] = menu_item.get("nama", "")
            item["price"] = int(menu_item.get("harga", 0))
            total_price += item["price"] * item["quantity"]

          

        order_id = db.orders.count_documents({}) + 1

        order = {
            "order_id": order_id,
            "user_email": user_email,
            "order_items": cart_items,
            "total_price": total_price,
            "status": "NEW",
            "timestamp": datetime.now(),
        }

        db.orders.insert_one(order)
      
        for i in cart_items:
            db.menu.update_one(
                {"menuId": i["menuId"]}, {"$set": {"sold": +i["quantity"]}}
            )
        db.users.update_one({"email": user_email}, {"$set": {"cart": []}})

        return jsonify(
            {"success": True, "message": "Purchase confirmed and cart cleared"}
        )

    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Your token has expired"})
    except jwt.exceptions.DecodeError:
        return jsonify(
            {"success": False, "message": "There was a problem logging you in"}
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/remove_item", methods=["POST"])
def remove_item():
    token_receive = request.cookies.get("mytoken")
    item_id = request.form.get("item_id")  # Unique item identifier
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_email = payload["id"]

        db.users.update_one(
            {"email": user_email},
            {
                "$pull": {"cart": {"item_id": item_id}}
            },  # Match the unique item identifier
        )

        return jsonify({"success": True, "message": "Item removed successfully"})
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Your token has expired"})
    except jwt.exceptions.DecodeError:
        return jsonify(
            {"success": False, "message": "There was a problem logging you in"}
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/apply_voucher", methods=["POST"])
def apply_voucher():
    token_receive = request.cookies.get("mytoken")
    voucher_code = request.form.get("voucher_code")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]})
        cart_items = user_info.get("cart", [])

        total_price = 0
        for item in cart_items:
            menu_item = get_menu_item(item["menuId"])
            item["name"] = menu_item["nama"]
            item["price"] = int(menu_item["harga"])
            item_total = item["price"] * item["quantity"]
            total_price += item_total

        voucher = db.vouchers.find_one({"code": voucher_code})
        if voucher and voucher["is_valid"]:
            discount = int(voucher["discount"])
        else:
            discount = 0

        tax = total_price * 0.10
        final_total_price = total_price - discount + tax

        return jsonify(
            {
                "total_price": total_price,
                "discount": discount,
                "tax": tax,
                "final_total_price": final_total_price,
                "success": True if discount > 0 else False,
                "message": (
                    "Voucher applied successfully"
                    if discount > 0
                    else "Invalid voucher code"
                ),
            }
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Your token has expired"})
    except jwt.exceptions.DecodeError:
        return jsonify(
            {"success": False, "message": "There was a problem logging you in"}
        )


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    token_receive = request.cookies.get("mytoken")
    if not token_receive:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})

        menuId = request.form.get("menuId")
        quantity = int(request.form.get("quantity"))  
        option1 = request.form.get("option1")
        option2 = request.form.getlist("option2") 

        cart_item = {
            "item_id": str(uuid4()),
            "menuId": menuId,
            "quantity": quantity,
            "option1": option1,
            "option2": option2,
        }
    
        if not user_info.get("cart"):
            user_info["cart"] = []

        item_exists = False
        for item in user_info["cart"]:
            if (
                item["menuId"] == menuId
                and item["option1"] == option1
                and item["option2"] == option2
            ):
                item["quantity"] += quantity
                item_exists = True
                break

        if not item_exists:
            user_info["cart"].append(cart_item)

        db.users.update_one(
            {"email": payload["id"]}, {"$set": {"cart": user_info["cart"]}}
        )

        return jsonify({"success": True})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({"success": False, "message": "Invalid token"}), 403
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/product/<menuId>", methods=["GET", "POST"])
def product(menuId):
    token_receive = request.cookies.get("mytoken")
    user_info = None
    if token_receive:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
        except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
            pass

    menu_item = db.menu.find_one({"menuId": menuId}, {"_id": False})
    
    price_item = locale.format_string("Rp. %d", int(menu_item["harga"]), grouping=True)
  

    if not menu_item:
        return "Menu item not found", 404

    similar_menu = list(
        db.menu.find({"kategori": {"$in": menu_item["kategori"]}}, {"_id": False})
    )
    for item in similar_menu:
        total_ratings = sum([item.get(f"rating_{i}", 0) * i for i in range(1, 6)])
        total_reviews = sum([item.get(f"rating_{i}", 0) for i in range(1, 6)])
        item["average_rating"] = (
            total_ratings / total_reviews if total_reviews > 0 else 0
        )
        item["harga"] = locale.format_string(
            "Rp. %d", int(item["harga"]), grouping=True
        )

    reviews = list(db.reviews.find({"item_id": menuId}))
    reviews_total = len(reviews)
    for review in reviews:
        user = db.users.find_one({"email": review["user_email"]}, {"_id": False})
        if user:
            review["user_name"] = user["user_name"]
        else:
            review["user_name"] = "Unknown User"

    total_reviews = sum(menu_item.get(f"rating_{i}", 0) for i in range(1, 6))
    if total_reviews > 0:
        star_percentages = {}
        for i in range(1, 6):
            rating_key = f"rating_{i}"
            count = menu_item.get(rating_key, 0)
            percentage = (count / total_reviews) * 100
            star_percentages[i] = round(percentage, 2)
    else:
        star_percentages = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    if total_reviews > 0:
        total_rating = sum(i * menu_item.get(f"rating_{i}", 0) for i in range(1, 6))
        average_rating = total_rating / total_reviews
        average_rating = round(average_rating, 1)
    else:
        average_rating = 0

    similar_menu = similar_menu[:4]
    return render_template(
        "product.html",
        user_info=user_info,
        similar_menu=similar_menu,
        menu_item=menu_item,
        item_price=price_item,
        reviews=reviews,
        star_percentages=star_percentages,
        average_rating=average_rating,
        total_reviews=reviews_total,
    )


@app.route("/update_profile", methods=["POST"])
def update_profile():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_email = payload["id"]
        full_name = request.form.get("fullName")
        email = request.form.get("email")
        old_password = request.form.get("oldPassword")
        new_password = request.form.get("newPassword")
        image_url = ""
        
        image_file = request.files.get('image_file')
        print(image_file)
        if image_file:
            filename = secure_filename(image_file.filename)
            filename1 = secure_filename(full_name)
            finalFilename = f"{filename1}.{filename.split('.')[-1]}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)
            
            try:
                imagekit = ImageKit(
                    private_key=PRIVATE_KEY_TOKEN_IMAGEKIT,
                    public_key=PUBLIC_KEY_TOKEN_IMAGEKIT,
                    url_endpoint='https://ik.imagekit.io/coffeeshopteam3'
                )
                response = imagekit.upload_file(
                    file=open(filepath, 'rb'),
                    file_name=finalFilename,
                )
                image_url = response.response_metadata.raw['url']
                print(image_url)
                os.remove(filepath)
            except Exception as e:
                os.remove(filepath)
                return jsonify({"message": "Error occurred while uploading image. " + str(e)}), 500
            
        
        
        
        db.users.update_one(
            {"email": user_email},
            {
                "$set": {
                    "user_name": full_name,
                    "email": email,
                    "profile_image": image_url
                }
            },
        )

        return redirect(url_for("profile"))

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError) as e:
        return redirect(url_for("login"))


@app.route("/register/", methods=["GET", "POST"])
def register():

    return render_template("register.html")


@app.route("/prepare_login", methods=["POST"])
def prepare_login():
    email = request.form.get("email")
    return redirect(url_for("login", email=email))


@app.route("/login/", methods=["GET", "POST"])
def login():
    msg = request.args.get("msg")
    email = request.args.get("email", "")
    token_receive = request.cookies.get("mytoken")
 
    if token_receive:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.users.find_one({"email": payload["id"]})
          
            return render_template("index.html", user_info=user_info)
        except jwt.ExpiredSignatureError:
            return redirect(url_for("login", msg="Your token has expired"))
        except jwt.exceptions.DecodeError:
            return redirect(url_for("login", msg="There was problem logging you in"))
    return render_template("login.html", msg=msg, email=email)


@app.route("/sign_up/save", methods=["POST"])
def sign_up():
    name_receive = request.form["name_give"]
    email_receive = request.form["email_give"]
    password_receive = request.form["password_give"]
   
    password_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    doc = {
        "user_name": name_receive,
        "email": email_receive,
        "password": password_hash,
        "role": "USER",
        "profile_image": "https://ik.imagekit.io/somnium/images.png",
    }
    db.users.insert_one(doc)
    return jsonify({"result": "success"})


@app.route("/sign_in", methods=["POST"])
def sign_in():
    email_receive = request.form["email_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    
    result = db.users.find_one(
        {
            "email": email_receive,
            "password": pw_hash,
        }
    )
    if result:
        payload = {
            "id": email_receive,
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify(
            {
                "result": "success",
                "token": token,
            }
        )

    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "We could not find a user with that id/password combination",
            }
        )


def generate_menu_id(categories):
    initial_id = "".join([category[0].upper() for category in categories])

    existing_ids = db.menu.find({"menuId": {"$regex": f"^{initial_id}"}})

    max_number = 0
    for existing_id in existing_ids:
        match = re.match(rf"^{initial_id}(\d+)$", existing_id["menuId"])
        if match:
            number = int(match.group(1))
            if number > max_number:
                max_number = number

    new_number = max_number + 1
    new_menu_id = f"{initial_id}{new_number:02d}"

    return new_menu_id




# ===================================== ADMIN =====================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token_receive = request.cookies.get("mytoken")
        if not token_receive:
            return redirect(url_for('login'))

        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_email = payload["id"]
            user = db.users.find_one({"email": user_email})
            if user and user.get("role") == "ADMIN":
                return f(*args, **kwargs)
            else:
                return render_template("unauthorized.html", message="Unauthorized access")
        except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
            return redirect(url_for('login')) 
        except Exception as e:
            return render_template("error.html", error=str(e))

    return decorated_function


# Routes
@app.route("/dashboard/", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    token_receive = request.cookies.get("mytoken")
    if not token_receive:
        return redirect(url_for("login"))

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
        if user_info['profile_image'] == None:
            user_info["profile_image"] = 'https://ik.imagekit.io/coffeeshopteam3/profile_placeholdesr.png'
        if not user_info:
            return redirect(url_for("login"))
        print(user_info)
        return render_template(
            "admin_dashboard.html", user_info=user_info
        )

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))
 


@app.route("/admin_user_list/", methods=["GET", "POST"])
@admin_required
def admin_user_list():
    token_receive = request.cookies.get("mytoken")
    if not token_receive:
        return redirect(url_for("login"))

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
        if user_info['profile_image'] == None:
            user_info["profile_image"] = 'https://ik.imagekit.io/coffeeshopteam3/profile_placeholdesr.png'
        if not user_info:
            return redirect(url_for("login"))
        return render_template(
            "admin_user_list.html", user_info=user_info
        )

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/admin_update_menu/", methods=["GET", "POST"])
@admin_required
def admin_update_menu():
    menus = list(db.menu.find({}, {"_id": False}))
    for menu in menus:
        try:
            menu["harga"] = locale.format_string("%d", int(menu["harga"]), grouping=True)
        except (ValueError, TypeError):
            menu["harga"] = menu.get("harga", "0")
    token_receive = request.cookies.get("mytoken")
    if not token_receive:
        return redirect(url_for("login"))

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
        if user_info['profile_image'] == None:
            user_info["profile_image"] = 'https://ik.imagekit.io/coffeeshopteam3/profile_placeholdesr.png'
        if not user_info:
            return redirect(url_for("login"))
        return render_template(
            "admin_update_menu.html", user_info=user_info, menus=menus
        )

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/admin_add_product/", methods=["GET", "POST"])
@admin_required
def admin_add_product():
    token_receive = request.cookies.get("mytoken")
    if not token_receive:
        return redirect(url_for("login"))

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.users.find_one({"email": payload["id"]}, {"_id": False})
        if user_info['profile_image'] == None:
            user_info["profile_image"] = 'https://ik.imagekit.io/coffeeshopteam3/profile_placeholdesr.png'
        if not user_info:
            return redirect(url_for("login"))
        return render_template(
            "admin_add_product.html", user_info=user_info
        )

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/api/overview", methods=["GET"])
@admin_required
def get_overview():
    turnover = db.orders.aggregate(
        [{"$group": {"_id": None, "total": {"$sum": "$total_price"}}}]
    ).next()["total"]
    profit = turnover * 0.2 
    new_customers = db.orders.distinct("user_email")
    customers = db.users.count_documents({})
    

    overview_data = {
        "turnover": turnover,
        "profit": profit,
        "new_customers": customers,
    }

    return jsonify(overview_data)


@app.route("/api/orders", methods=["GET"])
@admin_required
def get_detailed_report():
    orders = db.orders.find()
    
    orders_list = []

    for order in orders:
        name = db.users.find_one({"email": order["user_email"]})["user_name"]
        
        for item in order["order_items"]:
            if isinstance(item["option2"], list):
                    item["option2"] = ", ".join(item["option2"])
            orders_list.append(
                {
                    "order_id": order["order_id"],
                    "name": name,
                    "menu": item["name"] + " | " + item["option1"] + " , " + item["option2"],
                    "value": item["price"],
                    "date": order["timestamp"].strftime("%d/%m/%Y"),
                    "status": order["status"],
                }
            )
    status_order = {"NEW": 1, "IN-PROGRESS": 2, "COMPLETED": 3}
    orders_list.sort(key=lambda x: status_order.get(x["status"], 4))
    
    return jsonify(orders_list)


@app.route("/update_order_status", methods=["POST"])
@admin_required
def update_order_status():
    try:
        order_id = request.json.get("order_id")
        new_status = request.json.get("status")

        if not order_id or not new_status:
            return jsonify({"success": False, "message": "Missing order ID or status"}), 400

        db.orders.update_one({"order_id": order_id}, {"$set": {"status": new_status}})

        return jsonify({"success": True, "message": "Order status updated successfully"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/update_role", methods=["POST"])
@admin_required
def update_role():
    try:
        email = request.json.get("email")
        role = request.json.get("roles")

        if not email or not role:
            return jsonify({"success": False, "message": "Missing Email or role"}), 400

        db.users.update_one({"email": email}, {"$set": {"role": role}})

        return jsonify({"success": True, "message": "Role updated successfully"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500



@app.route("/api/users")
@admin_required
def api_users():
    users = list(db.users.find({}))
    user_data = []
    for user in users:
        user_data.append(
            {
                "email": user["email"],
                "user_name": user["user_name"],
                "role": user["role"],
            }
        )
    user_order = {"ADMIN": 1, "USER": 2}
    user_data.sort(key=lambda x: user_order.get(x["role"], 4))

    return jsonify(user_data)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html")
    else:
        nama = request.form.get("productName")
        harga = request.form.get("productPrice")
        deskripsi = request.form.get("productDescription")
        kategori = request.form.getlist("kategori")
        image_url = request.form.get("image")

        menu_id = generate_menu_id(kategori)

        menu = {
            "menuId": menu_id,
            "nama": nama,
            "harga": harga,
            "deskripsi": deskripsi,
            "kategori": kategori,
            "image": image_url,
            "sold": 0,
        }
        db.menu.insert_one(menu)
        return jsonify({"result": "success"})



@app.route('/uploads', methods=['POST'])
@admin_required
def uploads():
    nama = request.form.get("productName")
    harga = request.form.get("productPrice")
    deskripsi = request.form.get("productDescription")
    kategori = request.form.getlist("kategori")
    menu_id = generate_menu_id(kategori)
    image_url = ""
    
    image_name = nama
    image_file = request.files['image_file']
    filename = secure_filename(image_file.filename)
    
    filename1 = secure_filename(image_name)
    
    
    finalFilename = f"{filename1}.{filename.split(".")[-1]}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_file.save(filepath)
    try:
        imagekit = ImageKit(
            private_key=PRIVATE_KEY_TOKEN_IMAGEKIT,
            public_key=PUBLIC_KEY_TOKEN_IMAGEKIT,
            url_endpoint='https://ik.imagekit.io/somnium'
        )

        response = imagekit.upload_file(
            file=open(filepath, 'rb'),
            file_name=finalFilename,
        )
        
        image_url = response.response_metadata.raw['url']
        product_data = {
            "menuId": menu_id,
            "nama": nama,
            "harga": harga,
            "deskripsi": deskripsi,
            "kategori": kategori,
            "image": image_url,
            "sold"  :0
        }

        db.menu.insert_one(product_data)
        os.remove(filepath)
        return redirect(url_for("admin_add_product"))
    except Exception as e:
        os.remove(filepath)
        return jsonify({"message": "Error occurred while uploading image. " + str(e)}),



@app.route('/remove_product', methods=['POST'])
@admin_required
def remove_product():
    product_id = request.form.get("productId")
    db.menu.delete_one({"menuId": product_id})
    return redirect(url_for("admin_update_menu"))

@app.route('/edit_product', methods=['POST'])
@admin_required
def edit_product():
    product_id = request.form.get("productId")
    nama = request.form.get("productName")
    harga = request.form.get("productPrice")
    deskripsi = request.form.get("productDescription")
    image_url = request.form.get("currentImage")

    image_file = request.files.get('image_file')
    if image_file:
        filename = secure_filename(image_file.filename)
        filename1 = secure_filename(nama)
        finalFilename = f"{filename1}.{filename.split('.')[-1]}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(filepath)
        
        try:
            imagekit = ImageKit(
                private_key=PRIVATE_KEY_TOKEN_IMAGEKIT,
                public_key=PUBLIC_KEY_TOKEN_IMAGEKIT,
                url_endpoint='https://ik.imagekit.io/coffeeshopteam3'
            )
            response = imagekit.upload_file(
                file=open(filepath, 'rb'),
                file_name=finalFilename,
            )
            image_url = response.response_metadata.raw['url']
            os.remove(filepath)
        except Exception as e:
            os.remove(filepath)
            return jsonify({"message": "Error occurred while uploading image. " + str(e)}), 500

    db.menu.update_one(
        {"menuId": product_id},
        {"$set": {
            "nama": nama,
            "harga": harga,
            "deskripsi": deskripsi,
            "image": image_url
        }}
    )

    return redirect(url_for("admin_update_menu"))


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
