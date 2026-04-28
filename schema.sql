-- Production-ready PostgreSQL schema for Business Analytics Chatbot
-- Normalized to 3NF with proper indexing

-- Drop tables if they exist (for clean recreation)
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

-- Users table
-- Stores customer information
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    country VARCHAR(100) NOT NULL,
    CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Products table
-- Stores product catalog
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    CONSTRAINT price_positive CHECK (price > 0)
);

-- Orders table
-- Stores order header information
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12, 2) NOT NULL CHECK (total_amount >= 0),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT total_amount_non_negative CHECK (total_amount >= 0)
);

-- Order Items table
-- Stores individual items in each order (junction table for many-to-many relationship)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    CONSTRAINT quantity_positive CHECK (quantity > 0),
    CONSTRAINT price_positive CHECK (price > 0)
);

-- Create indexes for performance
-- Index on users.email for fast lookups
CREATE INDEX idx_users_email ON users(email);

-- Index on users.country for analytics queries
CREATE INDEX idx_users_country ON users(country);

-- Index on users.created_at for time-based queries
CREATE INDEX idx_users_created_at ON users(created_at);

-- Index on products.category for filtering
CREATE INDEX idx_products_category ON products(category);

-- Index on orders.user_id for joining with users
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Index on orders.order_date for time-based analytics
CREATE INDEX idx_orders_order_date ON orders(order_date);

-- Index on orders.total_amount for revenue analysis
CREATE INDEX idx_orders_total_amount ON orders(total_amount);

-- Index on order_items.order_id for joining with orders
CREATE INDEX idx_order_items_order_id ON order_items(order_id);

-- Index on order_items.product_id for joining with products
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

-- Composite index for common analytics queries (orders by user and date)
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);

-- Composite index for order items by order and product
CREATE INDEX idx_order_items_order_product ON order_items(order_id, product_id);
