-- Create DB & user (ask your local MySQL root to run this once)
CREATE DATABASE food_app CHARACTER SET utf8mb4;
CREATE USER 'fooduser'@'localhost' IDENTIFIED BY 'foodpass';
GRANT ALL PRIVILEGES ON food_app.* TO 'fooduser'@'localhost';
FLUSH PRIVILEGES;

USE food_app;

-- Tables
CREATE TABLE menu_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  category VARCHAR(50),
  price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
  is_active TINYINT NOT NULL DEFAULT 1
);

CREATE TABLE orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_name VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  order_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0)
);

CREATE TABLE order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  item_id INT NOT NULL,
  qty INT NOT NULL CHECK (qty > 0),
  line_total DECIMAL(10,2) NOT NULL CHECK (line_total >= 0),
  FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (item_id) REFERENCES menu_items(id)
);

-- Seed menu (example)
INSERT INTO menu_items (name, category, price) VALUES
('Margherita Pizza','Pizza',199),
('Paneer Tikka Pizza','Pizza',279),
('Veg Burger','Burger',99),
('French Fries','Sides',79),
('Coke 300ml','Beverage',49);
