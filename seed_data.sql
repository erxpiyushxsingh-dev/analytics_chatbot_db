-- Seed Data for Business Analytics Chatbot
-- This file contains realistic test data with logical consistency

-- Insert Users (12 users)
INSERT INTO users (name, email, created_at, country) VALUES
('John Smith', 'john.smith@email.com', '2023-01-15 10:30:00+00', 'USA'),
('Emma Johnson', 'emma.johnson@email.com', '2023-02-20 14:45:00+00', 'UK'),
('Michael Chen', 'michael.chen@email.com', '2023-03-10 09:15:00+00', 'Canada'),
('Sarah Williams', 'sarah.williams@email.com', '2023-04-05 16:20:00+00', 'Australia'),
('David Brown', 'david.brown@email.com', '2023-05-12 11:00:00+00', 'USA'),
('Lisa Garcia', 'lisa.garcia@email.com', '2023-06-18 13:30:00+00', 'Spain'),
('James Wilson', 'james.wilson@email.com', '2023-07-22 08:45:00+00', 'UK'),
('Maria Martinez', 'maria.martinez@email.com', '2023-08-30 15:10:00+00', 'Mexico'),
('Robert Taylor', 'robert.taylor@email.com', '2023-09-14 10:55:00+00', 'Canada'),
('Jennifer Davis', 'jennifer.davis@email.com', '2023-10-25 12:40:00+00', 'USA'),
('Thomas Anderson', 'thomas.anderson@email.com', '2023-11-08 09:25:00+00', 'Germany'),
('Amanda White', 'amanda.white@email.com', '2023-12-03 14:50:00+00', 'Australia');

-- Insert Products (15 products across different categories)
INSERT INTO products (name, category, price) VALUES
('Laptop Pro 15', 'Electronics', 1299.99),
('Wireless Mouse', 'Electronics', 49.99),
('Mechanical Keyboard', 'Electronics', 149.99),
('27" Monitor 4K', 'Electronics', 399.99),
('USB-C Hub', 'Electronics', 79.99),
('Office Chair Ergonomic', 'Furniture', 349.99),
('Standing Desk', 'Furniture', 599.99),
('Bookshelf Modern', 'Furniture', 199.99),
('Desk Lamp LED', 'Furniture', 89.99),
('Coffee Table', 'Furniture', 249.99),
('Notebook Premium', 'Stationery', 19.99),
('Pen Set Luxury', 'Stationery', 39.99),
('Desk Organizer', 'Stationery', 29.99),
('Calendar 2024', 'Stationery', 14.99),
('Whiteboard A3', 'Stationery', 49.99);

-- Insert Orders (12 orders, one per user)
INSERT INTO orders (user_id, order_date, total_amount) VALUES
(1, '2024-01-10 10:30:00+00', 1549.97),
(2, '2024-01-15 14:20:00+00', 649.98),
(3, '2024-02-05 09:45:00+00', 1299.99),
(4, '2024-02-12 16:30:00+00', 899.98),
(5, '2024-03-01 11:15:00+00', 449.98),
(6, '2024-03-18 13:50:00+00', 1999.97),
(7, '2024-04-02 08:25:00+00', 79.99),
(8, '2024-04-20 15:40:00+00', 549.98),
(9, '2024-05-10 10:00:00+00', 949.97),
(10, '2024-05-25 12:55:00+00', 349.99),
(11, '2024-06-08 09:10:00+00', 229.97),
(12, '2024-06-15 14:35:00+00', 1799.96);

-- Insert Order Items (30 items with logical consistency)
-- Order 1: User 1 bought Laptop Pro + Wireless Mouse + USB-C Hub
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 1299.99),
(1, 2, 1, 49.99),
(1, 5, 2, 79.99);

-- Order 2: User 2 bought Mechanical Keyboard + 27" Monitor
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(2, 3, 1, 149.99),
(2, 4, 1, 399.99),
(2, 5, 1, 79.99);

-- Order 3: User 3 bought Laptop Pro
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(3, 1, 1, 1299.99);

-- Order 4: User 4 bought Office Chair + Desk Lamp
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(4, 6, 1, 349.99),
(4, 9, 1, 89.99),
(4, 10, 1, 249.99),
(4, 5, 1, 79.99);

-- Order 5: User 5 bought Standing Desk
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(5, 7, 1, 599.99),
(5, 9, 1, 89.99),
(5, 5, 1, 79.99);

-- Order 6: User 6 bought Laptop Pro + Office Chair + Standing Desk
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(6, 1, 1, 1299.99),
(6, 6, 1, 349.99),
(6, 7, 1, 599.99);

-- Order 7: User 7 bought USB-C Hub only
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(7, 5, 1, 79.99);

-- Order 8: User 8 bought Bookshelf + Desk Lamp + Coffee Table
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(8, 8, 1, 199.99),
(8, 9, 1, 89.99),
(8, 10, 1, 249.99),
(8, 5, 1, 79.99);

-- Order 9: User 9 bought 27" Monitor + Mechanical Keyboard + Wireless Mouse
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(9, 4, 1, 399.99),
(9, 3, 1, 149.99),
(9, 2, 1, 49.99),
(9, 9, 1, 89.99),
(9, 5, 1, 79.99);

-- Order 10: User 10 bought Office Chair
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(10, 6, 1, 349.99);

-- Order 11: User 11 bought Stationery items
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(11, 11, 5, 19.99),
(11, 12, 1, 39.99),
(11, 13, 2, 29.99),
(11, 5, 1, 79.99);

-- Order 12: User 12 bought Laptop Pro + Standing Desk + Bookshelf
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(12, 1, 1, 1299.99),
(12, 7, 1, 599.99),
(12, 8, 1, 199.99),
(12, 9, 1, 89.99),
(12, 5, 1, 79.99);
