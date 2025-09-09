import mysql.connector
from mysql.connector import Error
from datetime import date
from decimal import Decimal

# ---- DB CONFIG (change if needed) ----
DB_CFG = {
    "host": "localhost",
    "user": "fooduser",
    "password": "foodpass",
    "database": "food_app",
}

def get_conn():
    return mysql.connector.connect(**DB_CFG)

# ---------- Core Features ----------
def show_menu():
    with get_conn() as con:
        cur = con.cursor(dictionary=True)
        cur.execute("SELECT id, name, category, price FROM menu_items WHERE is_active=1 ORDER BY category, name")
        rows = cur.fetchall()
    print("\n--- MENU ---")
    for r in rows:
        print(f"{r['id']:>2} | {r['name']:<22} | {r['category'] or '-':<10} | ₹{r['price']:.2f}")
    return rows

def place_order():
    name = input("Customer name: ").strip()
    phone = input("Phone: ").strip()
    cart = []

    while True:
        show_menu()
        item = input("Enter item id (blank to checkout): ").strip()
        if item == "":
            break
        try:
            qty = int(input("Qty: ").strip())
            cart.append((int(item), qty))
        except ValueError:
            print("Invalid input. Try again.")

    if not cart:
        print("No items selected.")
        return

    try:
        with get_conn() as con:
            cur = con.cursor(dictionary=True)
            # compute bill
            total = Decimal("0.00")
            lines = []
            for item_id, qty in cart:
                cur.execute("SELECT name, price FROM menu_items WHERE id=%s AND is_active=1", (item_id,))
                row = cur.fetchone()
                if not row:
                    print(f"Item {item_id} not found, skipped.")
                    continue
                line_total = Decimal(str(row["price"])) * qty
                total += line_total
                lines.append((item_id, qty, line_total))

            if not lines:
                print("Nothing valid to place.")
                return

            # create order
            cur.execute(
                "INSERT INTO orders(customer_name, phone, total_amount) VALUES (%s, %s, %s)",
                (name, phone, total),
            )
            order_id = cur.lastrowid

            # items
            cur.executemany(
                "INSERT INTO order_items(order_id, item_id, qty, line_total) VALUES (%s, %s, %s, %s)",
                [(order_id, i, q, str(lt)) for i, q, lt in lines],
            )
            con.commit()

        print(f"\nOrder #{order_id} placed successfully. Total: ₹{total:.2f}")
    except Error as e:
        print("DB error:", e)

def order_history():
    phone = input("Enter phone to view history: ").strip()
    with get_conn() as con:
        cur = con.cursor(dictionary=True)
        cur.execute(
            "SELECT id, order_time, total_amount FROM orders WHERE phone=%s ORDER BY order_time DESC",
            (phone,),
        )
        orders = cur.fetchall()
        if not orders:
            print("No orders found.")
            return

        print(f"\n--- Order history for {phone} ---")
        for o in orders:
            print(f"Order #{o['id']:>3} | {o['order_time']} | ₹{o['total_amount']:.2f}")
            cur.execute("""
                SELECT mi.name, oi.qty, oi.line_total
                FROM order_items oi
                JOIN menu_items mi ON mi.id = oi.item_id
                WHERE oi.order_id=%s
            """, (o["id"],))
            items = cur.fetchall()
            for it in items:
                print(f"   - {it['name']} x{it['qty']}  ₹{it['line_total']:.2f}")

def daily_sales_report():
    d = input("Report date YYYY-MM-DD (blank=today): ").strip()
    if not d:
        d = date.today().isoformat()

    with get_conn() as con:
        cur = con.cursor(dictionary=True)
        # totals
        cur.execute("""
            SELECT COUNT(*) AS orders_count, COALESCE(SUM(total_amount),0) AS gross
            FROM orders
            WHERE DATE(order_time) = %s
        """, (d,))
        totals = cur.fetchone()

        # top items
        cur.execute("""
            SELECT mi.name, SUM(oi.qty) AS qty_sold, SUM(oi.line_total) AS revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN menu_items mi ON mi.id = oi.item_id
            WHERE DATE(o.order_time) = %s
            GROUP BY mi.name
            ORDER BY revenue DESC
            LIMIT 5
        """, (d,))
        top = cur.fetchall()

    print(f"\n--- Daily Sales Report: {d} ---")
    print(f"Total Orders : {totals['orders_count']}")
    print(f"Gross Sales  : ₹{Decimal(str(totals['gross'])):.2f}")
    print("Top Items:")
    if top:
        for t in top:
            print(f" - {t['name']} | Qty: {t['qty_sold']} | Rev: ₹{Decimal(str(t['revenue'])):.2f}")
    else:
        print(" (no sales)")

def admin_add_menu_item():
    name = input("Item name: ").strip()
    category = input("Category: ").strip() or None
    price = input("Price (e.g., 199): ").strip()
    with get_conn() as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO menu_items(name, category, price, is_active) VALUES (%s, %s, %s, 1)",
            (name, category, price),
        )
        con.commit()
    print("Added.")

# ---------- CLI ----------
def main():
    while True:
        print("\n1) Show Menu\n2) Place Order\n3) Order History\n4) Daily Sales Report\n5) Admin: Add Menu Item\n0) Exit")
        ch = input("Choose: ").strip()
        if ch == "1": show_menu()
        elif ch == "2": place_order()
        elif ch == "3": order_history()
        elif ch == "4": daily_sales_report()
        elif ch == "5": admin_add_menu_item()
        elif ch == "0": break
        else: print("Invalid choice")

if __name__ == "__main__":
    main()
