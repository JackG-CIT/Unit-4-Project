from flask import Flask, request, render_template
import requests
import psycopg2
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Upload config
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# DB connection
def get_conn():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "goldeninvest"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
    )


# Initialize database
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Items table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS goldeninvest_items (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            stock INTEGER NOT NULL,
            image TEXT
        );
    """)

    # Transactions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS goldeninvest_transactions (
            id SERIAL PRIMARY KEY,
            item TEXT,
            amount INTEGER,
            status TEXT
        );
    """)

    # Ensure image column exists
    cur.execute("""
        ALTER TABLE goldeninvest_items
        ADD COLUMN IF NOT EXISTS image TEXT;
    """)

    # Insert starter data if empty
    cur.execute("SELECT COUNT(*) FROM goldeninvest_items")
    count = cur.fetchone()[0]

    if count == 0:
        cur.execute("""
            INSERT INTO goldeninvest_items (name, price, stock)
            VALUES 
            ('Mr. Smith', 10, 5),
            ('Ms. Johnson', 15, 3);
        """)

    conn.commit()
    cur.close()
    conn.close()


# Home page
@app.route("/", methods=["GET"])
def home():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT name, price, stock, image FROM goldeninvest_items")
    rows = cur.fetchall()

    items = [
        {
            "name": row[0],
            "price": row[1],
            "stock": row[2],
            "image": row[3]
        }
        for row in rows
    ]

    cur.close()
    conn.close()

    return render_template("index.html", items=items)


# Buy item
@app.route("/buy", methods=["POST"])
def buy():
    item = request.form.get("item")
    amount = request.form.get("amount")

    if not item or not amount:
        return "Invalid input"

    conn = get_conn()
    cur = conn.cursor()

    # Check stock
    cur.execute(
        "SELECT stock FROM goldeninvest_items WHERE name=%s",
        (item,)
    )
    result_stock = cur.fetchone()

    if not result_stock or result_stock[0] <= 0:
        cur.close()
        conn.close()
        return "Out of stock! <br><a href='/'>Go back</a>"

    # Call payment service
    try:
        response = requests.post("http://payment:5001/pay", json={
            "amount": amount
        })
        payment_status = response.json().get("status", "error")
    except:
        payment_status = "service unavailable"

    # Update stock if success
    if payment_status == "success":
        cur.execute(
            "UPDATE goldeninvest_items SET stock = stock - 1 WHERE name=%s",
            (item,)
        )

    # Insert transaction
    cur.execute(
        "INSERT INTO goldeninvest_transactions (item, amount, status) VALUES (%s, %s, %s)",
        (item, amount, payment_status)
    )

    conn.commit()
    cur.close()
    conn.close()

    return f"Payment {payment_status}! <br><a href='/'>Go back</a>"


# Add item (WITH IMAGE SUPPORT)
@app.route("/add", methods=["POST"])
def add_item():
    try:
        name = request.form.get("name")
        price = int(request.form.get("price"))
        stock = int(request.form.get("stock"))
        image_file = request.files.get("image")

        if not name:
            return "Invalid input"

        filename = None

        # Handle image upload
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO goldeninvest_items (name, price, stock, image) VALUES (%s, %s, %s, %s)",
            (name, price, stock, filename)
        )

        conn.commit()
        cur.close()
        conn.close()

        return "Item added! <br><a href='/'>Go back</a>"

    except Exception as e:
        return f"Error: {str(e)}"


# Run app
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)