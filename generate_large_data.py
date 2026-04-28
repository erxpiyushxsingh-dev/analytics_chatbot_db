"""
Large seed data generator for D-Mart branches.
Generates realistic retail data with area-wise product performance.
"""

import random
import sqlite3
from datetime import datetime, timedelta

# Configuration
NUM_BRANCHES = 20
NUM_CUSTOMERS = 500
NUM_PRODUCTS = 100
NUM_ORDERS = 2000
NUM_ORDER_ITEMS = 5000

# D-Mart product categories
CATEGORIES = [
    "Groceries", "Electronics", "Home & Kitchen", "Clothing", 
    "Personal Care", "Beverages", "Snacks", "Dairy",
    "Fruits & Vegetables", "Household Essentials"
]

# Areas/locations
AREAS = [
    "Andheri West", "Bandra Kurla Complex", "Powai", "Thane West", "Navi Mumbai",
    "Malad", "Borivali", "Dadar", "Churchgate", "Colaba",
    "Sakinaka", "Kurla", "Ghatkopar", "Chembur", "Vashi",
    "Nerul", "Kharghar", "Panvel", "Kalyan", "Dombivali"
]

# Branch names
BRANCH_NAMES = [
    "D-Mart Andheri West", "D-Mart BKC", "D-Mart Powai", "D-Mart Thane West", "D-Mart Navi Mumbai",
    "D-Mart Malad", "D-Mart Borivali", "D-Mart Dadar", "D-Mart Churchgate", "D-Mart Colaba",
    "D-Mart Sakinaka", "D-Mart Kurla", "D-Mart Ghatkopar", "D-Mart Chembur", "D-Mart Vashi",
    "D-Mart Nerul", "D-Mart Kharghar", "D-Mart Panvel", "D-Mart Kalyan", "D-Mart Dombivali"
]

# Product names by category
PRODUCT_NAMES = {
    "Groceries": ["Rice 5kg", "Wheat Flour 10kg", "Sugar 5kg", "Salt 1kg", "Oil 1L", "Pulses 1kg", "Spices Set", "Tea 500g", "Coffee 200g", "Biscuits Pack"],
    "Electronics": ["Smartphone", "Headphones", "Bluetooth Speaker", "Power Bank", "USB Cable", "Charger", "Smart Watch", "Tablet", "Laptop", "Mouse"],
    "Home & Kitchen": ["Cooker 5L", "Non-stick Pan Set", "Blender", "Mixer Grinder", "Toaster", "Kettle", "Dinner Set", "Cutlery Set", "Storage Containers", "Mop"],
    "Clothing": ["Men's T-Shirt", "Women's Kurti", "Kids Dress", "Jeans", "Saree", "Shirt", "Trousers", "Jacket", "Sweater", "Innerwear"],
    "Personal Care": ["Shampoo", "Soap Pack", "Toothpaste", "Face Wash", "Lotion", "Deodorant", "Hair Oil", "Comb", "Razor", "Towel"],
    "Beverages": ["Cold Drink 2L", "Juice 1L", "Energy Drink", "Green Tea", "Coffee Powder", "Milk 1L", "Buttermilk", "Soda", "Mineral Water", "Mango Drink"],
    "Snacks": ["Chips Pack", "Namkeen", "Cookies", "Chocolate", "Candy", "Popcorn", "Nuts", "Dried Fruits", "Biscuits", "Cake"],
    "Dairy": ["Milk 1L", "Butter 100g", "Cheese 200g", "Curd 500g", "Paneer 200g", "Ghee 500g", "Cream 200g", "Yogurt", "Ice Cream", "Lassi"],
    "Fruits & Vegetables": ["Apples 1kg", "Bananas 1kg", "Onions 1kg", "Potatoes 1kg", "Tomatoes 1kg", "Carrots 500g", "Spinach 500g", "Oranges 1kg", "Grapes 500g", "Mangoes 1kg"],
    "Household Essentials": ["Detergent 1kg", "Dishwash Liquid", "Floor Cleaner", "Toilet Cleaner", "Broom", "Mop", "Bucket", "Trash Bags", "Tissues", "Napkins"]
}

# Customer names
FIRST_NAMES = ["Aarav", "Vihaan", "Aditya", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan", "Shaurya", "Atharv",
               "Ananya", "Diya", "Saanvi", "Aarohi", "Kavya", "Anvi", "Myra", "Pari", "Riya", "Siya",
               "Rahul", "Amit", "Vikram", "Rajesh", "Suresh", "Mahesh", "Deepak", "Sunil", "Ajay", "Vijay",
               "Priya", "Neha", "Pooja", "Sneha", "Rani", "Lakshmi", "Sunita", "Kavita", "Meena", "Anita"]

LAST_NAMES = ["Sharma", "Patel", "Singh", "Kumar", "Verma", "Gupta", "Malhotra", "Reddy", "Nair", "Iyer",
              "Jain", "Shah", "Mehta", "Desai", "Menon", "Pillai", "Chopra", "Bhatia", "Kapoor", "Khanna"]

def generate_random_date(start_date, end_date):
    """Generate random date between start and end."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def main():
    # Remove existing database
    import os
    db_path = "analytics.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema (SQLite-compatible)
    cursor.executescript("""
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS branches;

    CREATE TABLE branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        area TEXT NOT NULL
    );

    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        country TEXT NOT NULL,
        area TEXT NOT NULL,
        branch_id INTEGER,
        FOREIGN KEY (branch_id) REFERENCES branches(id)
    );

    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL CHECK (price > 0)
    );

    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        total_amount REAL NOT NULL CHECK (total_amount >= 0),
        branch_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (branch_id) REFERENCES branches(id)
    );

    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        price REAL NOT NULL CHECK (price > 0),
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
    );

    CREATE INDEX idx_users_email ON users(email);
    CREATE INDEX idx_users_area ON users(area);
    CREATE INDEX idx_users_branch ON users(branch_id);
    CREATE INDEX idx_products_category ON products(category);
    CREATE INDEX idx_orders_user_id ON orders(user_id);
    CREATE INDEX idx_orders_order_date ON orders(order_date);
    CREATE INDEX idx_orders_branch_id ON orders(branch_id);
    CREATE INDEX idx_order_items_order_id ON order_items(order_id);
    CREATE INDEX idx_order_items_product_id ON order_items(product_id);
    CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);
    CREATE INDEX idx_order_items_order_product ON order_items(order_id, product_id);
    """)
    print("Schema created")

    # Insert products
    print("Generating products...")
    product_id = 1
    for category in CATEGORIES:
        for name in PRODUCT_NAMES[category]:
            price = round(random.uniform(50, 5000), 2)
            cursor.execute(
                "INSERT INTO products (id, name, category, price) VALUES (?, ?, ?, ?)",
                (product_id, name, category, price)
            )
            product_id += 1
    print(f"Inserted {product_id - 1} products")

    # Insert branches
    print("Generating branches...")
    for i, branch_name in enumerate(BRANCH_NAMES, 1):
        area = AREAS[i - 1]
        cursor.execute(
            "INSERT INTO branches (id, name, area) VALUES (?, ?, ?)",
            (i, branch_name, area)
        )
    print(f"Inserted {len(BRANCH_NAMES)} branches")

    # Insert customers with area and branch
    print("Generating customers...")
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    for i in range(1, NUM_CUSTOMERS + 1):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}{i}@gmail.com"
        area = random.choice(AREAS)
        branch_id = random.randint(1, NUM_BRANCHES)
        created_at = generate_random_date(start_date, end_date).isoformat()
        
        cursor.execute(
            "INSERT INTO users (name, email, created_at, country, area, branch_id) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, created_at, "India", area, branch_id)
        )
    print(f"Inserted {NUM_CUSTOMERS} customers")

    # Insert orders
    print("Generating orders...")
    order_start_date = datetime(2024, 1, 1)
    order_end_date = datetime(2024, 12, 31)
    
    for i in range(1, NUM_ORDERS + 1):
        user_id = random.randint(1, NUM_CUSTOMERS)
        branch_id = random.randint(1, NUM_BRANCHES)
        order_date = generate_random_date(order_start_date, order_end_date).isoformat()
        
        # Generate order items first to calculate total
        num_items = random.randint(1, 5)
        total_amount = 0
        
        for _ in range(num_items):
            product_id = random.randint(1, NUM_PRODUCTS)
            quantity = random.randint(1, 5)
            cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
            price = cursor.fetchone()[0]
            total_amount += price * quantity
        
        cursor.execute(
            "INSERT INTO orders (user_id, order_date, total_amount, branch_id) VALUES (?, ?, ?, ?)",
            (user_id, order_date, round(total_amount, 2), branch_id)
        )
        order_id = cursor.lastrowid
        
        # Insert order items
        for _ in range(num_items):
            product_id = random.randint(1, NUM_PRODUCTS)
            quantity = random.randint(1, 5)
            cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
            price = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, product_id, quantity, price)
            )
    
    print(f"Inserted {NUM_ORDERS} orders")
    print(f"Inserted order items")

    # Verify
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables: {tables}")

    for table_name in tables:
        name = table_name[0]
        cursor.execute(f"SELECT COUNT(*) FROM {name}")
        count = cursor.fetchone()[0]
        print(f"  {name}: {count} rows")

    # Sample queries to verify data
    print("\n--- Sample Data Verification ---")
    cursor.execute("SELECT area, COUNT(*) as customer_count FROM users GROUP BY area ORDER BY customer_count DESC LIMIT 5")
    print("Top 5 areas by customers:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} customers")

    cursor.execute("SELECT category, COUNT(*) as product_count FROM products GROUP BY category")
    print("\nProducts by category:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} products")

    cursor.execute("SELECT branch_id, COUNT(*) as order_count FROM orders GROUP BY branch_id ORDER BY order_count DESC LIMIT 5")
    print("\nTop 5 branches by orders:")
    for row in cursor.fetchall():
        print(f"  Branch {row[0]}: {row[1]} orders")

    conn.commit()
    conn.close()
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    main()
