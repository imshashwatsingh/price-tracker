import requests
from bs4 import BeautifulSoup
import sqlite3
import schedule
import time
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
import random
from plyer import notification
import re
from tkinter import font

# Configure logging
logging.basicConfig(filename='price_tracker.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36'
]

# Database setup
def init_db():
    conn = sqlite3.connect('price_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  url TEXT UNIQUE,
                  name TEXT,
                  target_price REAL,
                  last_notified_price REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS price_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  product_id INTEGER,
                  price REAL,
                  timestamp TEXT,
                  FOREIGN KEY (product_id) REFERENCES products(id))''')
    conn.commit()
    conn.close()

# Scrape product details
def scrape_product(url):
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Amazon selectors with fallbacks
        name_elem = soup.select_one('#productTitle')
        price_elem = soup.select_one('.a-price-whole, #corePrice_feature_div .a-offscreen')

        if not name_elem or not price_elem:
            logging.error(f"Failed to scrape product name or price from {url}")
            return None, None

        name = name_elem.get_text().strip()
        price_text = price_elem.get_text().replace(',', '').strip()
        # Extract price with regex to handle formats like "$99.99" or "$100"
        price_match = re.search(r'\$?(\d+\.?\d*)', price_text)
        if not price_match:
            logging.error(f"Invalid price format for {url}: {price_text}")
            return None, None
        price = float(price_match.group(1))
        logging.info(f"Scraped {name} from {url}: ${price}")
        return name, price
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return None, None

# Send desktop notification
def send_notification(product_name, price, url):
    try:
        notification.notify(
            title=f"Price Drop Alert: {product_name}",
            message=f"The price of {product_name} has dropped to ${price:.2f}!\nCheck it out: {url}",
            timeout=10
        )
        logging.info(f"Notification sent for {product_name}: ${price:.2f}")
    except Exception as e:
        logging.error(f"Failed to send notification for {product_name}: {str(e)}")

# Check prices and update database
def check_prices():
    conn = sqlite3.connect('price_tracker.db')
    c = conn.cursor()
    c.execute("SELECT id, url, name, target_price, last_notified_price FROM products")
    products = c.fetchall()

    for product_id, url, name, target_price, last_notified_price in products:
        name, price = scrape_product(url)
        if price is None:
            continue

        # Insert price history
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("INSERT INTO price_history (product_id, price, timestamp) VALUES (?, ?, ?)",
                  (product_id, price, timestamp))

        # Check for price drop and avoid duplicate notifications
        if price <= target_price and (last_notified_price is None or price < last_notified_price):
            send_notification(name, price, url)
            c.execute("UPDATE products SET last_notified_price = ? WHERE id = ?", (price, product_id))

    conn.commit()
    conn.close()
    return timestamp

# Tooltip class for hover text
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert") if isinstance(self.widget, tk.Entry) else self.widget.bbox("current")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Segoe UI", 10))
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# GUI Application
class PriceTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Price Tracker Bot")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f4f8")  # Soft blue-gray background
        self.last_check_time = None

        # Fonts
        TITLE_FONT = ("Segoe UI", 24, "bold")
        LABEL_FONT = ("Segoe UI", 12)
        BUTTON_FONT = ("Segoe UI", 12, "bold")
        STATUS_FONT = ("Segoe UI", 10)

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton",
                        font=BUTTON_FONT,
                        padding=10,
                        background="#26a69a",  # Teal
                        foreground="#ffffff",
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="#4db6ac")
        style.map("TButton",
                  background=[("active", "#00897b")])  # Darker teal on hover
        style.configure("TLabel",
                        font=LABEL_FONT,
                        background="#f0f4f8",
                        foreground="#37474f")  # Dark gray
        style.configure("TEntry",
                        font=LABEL_FONT,
                        fieldbackground="#ffffff",
                        foreground="#37474f",
                        borderwidth=2)
        style.configure("Treeview",
                        background="#ffffff",
                        foreground="#37474f",
                        rowheight=28,
                        fieldbackground="#ffffff",
                        font=("Segoe UI", 11))
        style.configure("Treeview.Heading",
                        background="#26a69a",
                        foreground="#ffffff",
                        font=("Segoe UI", 12, "bold"))
        style.map("Treeview",
                  background=[("selected", "#b0bec5")],
                  foreground=[("selected", "#37474f")])

        # Header
        header = tk.Frame(root, bg="#26a69a", height=80)
        header.grid(row=0, column=0, columnspan=3, sticky="nsew")
        header.grid_propagate(False)
        tk.Label(header, text="Price Tracker Bot", bg="#26a69a", fg="#ffffff",
                 font=TITLE_FONT).pack(pady=20)

        # Input Frame
        input_frame = tk.Frame(root, bg="#f0f4f8", padx=20, pady=20)
        input_frame.grid(row=1, column=0, columnspan=3, sticky="ew")

        # URL Entry
        ttk.Label(input_frame, text="Product URL (Amazon):").grid(row=0, column=0, padx=(0, 10), pady=10, sticky="w")
        self.url_entry = ttk.Entry(input_frame, width=50)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)
        ToolTip(self.url_entry, "Enter an Amazon product URL")

        # Target Price Entry
        ttk.Label(input_frame, text="Target Price ($):").grid(row=1, column=0, padx=(0, 10), pady=10, sticky="w")
        self.price_entry = ttk.Entry(input_frame, width=15)
        self.price_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        ToolTip(self.price_entry, "Enter the desired price for notification")

        # Buttons
        button_frame = tk.Frame(root, bg="#f0f4f8")
        button_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")
        ttk.Button(button_frame, text="Add Product", command=self.add_product).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Check Prices Now", command=self.check_prices_now).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).pack(side=tk.RIGHT, padx=10)

        # Product List
        self.tree = ttk.Treeview(root, columns=("Name", "URL", "Target Price", "Latest Price"), show="headings", selectmode="browse")
        self.tree.heading("Name", text="Product Name", command=lambda: self.sort_column("Name", False))
        self.tree.heading("URL", text="URL", command=lambda: self.sort_column("URL", False))
        self.tree.heading("Target Price", text="Target Price ($)", command=lambda: self.sort_column("Target Price", False))
        self.tree.heading("Latest Price", text="Latest Price ($)", command=lambda: self.sort_column("Latest Price", False))
        self.tree.column("Name", width=250, anchor="w")
        self.tree.column("URL", width=300, anchor="w")
        self.tree.column("Target Price", width=120, anchor="center")
        self.tree.column("Latest Price", width=120, anchor="center")
        self.tree.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=3, column=2, sticky="ns", pady=10)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Action Buttons
        action_frame = tk.Frame(root, bg="#f0f4f8")
        action_frame.grid(row=4, column=0, columnspan=3, pady=10, sticky="ew")
        ttk.Button(action_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="View Price History", command=self.view_price_history).pack(side=tk.LEFT, padx=10)

        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Next check in 12 hours.")
        status_bar = tk.Label(root, textvariable=self.status_var, bg="#eceff1", fg="#37474f",
                              font=STATUS_FONT, anchor="w", relief=tk.SUNKEN, padx=10)
        status_bar.grid(row=5, column=0, columnspan=3, sticky="ew")

        # Configure grid weights
        root.grid_rowconfigure(3, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # Load products
        self.load_products()

        # Schedule price checks
        schedule.every(12).hours.do(self.check_prices_now)

    def add_product(self):
        url = self.url_entry.get().strip()
        target_price = self.price_entry.get().strip()

        if not url or not target_price:
            messagebox.showerror("Error", "Please enter both URL and target price.")
            return

        # Basic URL validation
        if not re.match(r'^https?://(www\.)?amazon\..+', url):
            messagebox.showerror("Error", "Please enter a valid Amazon  Amazon URL.")
            return

        try:
            target_price = float(target_price)
            if target_price <= 0:
                raise ValueError("Price must be positive.")
        except ValueError:
            messagebox.showerror("Error", "Target price must be a positive number.")
            return

        name, price = scrape_product(url)
        if not name:
            messagebox.showerror("Error", "Failed to scrape product. Check URL or try again.")
            return

        conn = sqlite3.connect('price_tracker.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO products (url, name, target_price, last_notified_price) VALUES (?, ?, ?, NULL)",
                      (url, name, target_price))
            product_id = c.lastrowid
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("INSERT INTO price_history (product_id, price, timestamp) VALUES (?, ?, ?)",
                      (product_id, price, timestamp))
            conn.commit()
            messagebox.showinfo("Success", f"Added {name[:30]}... to tracking list.")
            self.load_products()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "This URL is already being tracked.")
        finally:
            conn.close()

        self.url_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)

    def load_products(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = sqlite3.connect('price_tracker.db')
        c = conn.cursor()
        c.execute('''SELECT p.id, p.name, p.url, p.target_price, ph.price
                     FROM products p
                     LEFT JOIN (SELECT product_id, price, MAX(timestamp) as max_timestamp
                                FROM price_history
                                GROUP BY product_id) ph
                     ON p.id = ph.product_id''')
        for row in c.fetchall():
            name = row[1][:30] + "..." if len(row[1]) > 30 else row[1]
            url = row[2][:40] + "..." if len(row[2]) > 40 else row[2]
            self.tree.insert("", "end", values=(name, url, f"{row[3]:.2f}", f"{row[4]:.2f}" if row[4] else "N/A"))
            # Add tooltip for full text
            item_id = self.tree.get_children()[-1]
            ToolTip(self.tree, f"Name: {row[1]}\nURL: {row[2]}")
        conn.close()

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a product to remove.")
            return
        item = self.tree.item(selected[0])
        url = item['values'][1]
        if len(url) > 40:
            url = url[:40] + "..."
            c = sqlite3.connect('price_tracker.db').cursor()
            c.execute("SELECT url FROM products WHERE url LIKE ?", (url[:40] + '%',))
            url = c.fetchone()[0]
            c.close()
        confirm = messagebox.askyesno("Confirm Remove", f"Remove {item['values'][0]}?")
        if not confirm:
            return
        conn = sqlite3.connect('price_tracker.db')
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE url = ?", (url,))
        conn.commit()
        conn.close()
        self.load_products()
        messagebox.showinfo("Removed", "Product removed from tracking.")

    def clear_all(self):
        if not self.tree.get_children():
            messagebox.showwarning("Empty List", "No products to clear.")
            return
        confirm = messagebox.askyesno("Confirm Clear", "Remove all tracked products?")
        if not confirm:
            return
        conn = sqlite3.connect('price_tracker.db')
        c = conn.cursor()
        c.execute("DELETE FROM products")
        c.execute("DELETE FROM price_history")
        conn.commit()
        conn.close()
        self.load_products()
        messagebox.showinfo("Cleared", "All products removed.")

    def view_price_history(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a product to view history.")
            return
        item = self.tree.item(selected[0])
        url = item['values'][1]
        if len(url) > 40:
            url = url[:40] + "..."
            c = sqlite3.connect('price_tracker.db').cursor()
            c.execute("SELECT url FROM products WHERE url LIKE ?", (url[:40] + '%',))
            url = c.fetchone()[0]
            c.close()

        conn = sqlite3.connect('price_tracker.db')
        c = conn.cursor()
        c.execute("SELECT p.name, ph.price, ph.timestamp FROM products p JOIN price_history ph ON p.id = ph.product_id WHERE p.url = ?",
                  (url,))
        history = c.fetchall()
        conn.close()

        if not history:
            messagebox.showinfo("No History", "No price history available.")
            return

        # Create history window
        history_window = tk.Toplevel(self.root)
        history_window.title(f"Price History: {history[0][0][:30]}...")
        history_window.geometry("600x400")
        history_window.configure(bg="#f0f4f8")

        tree = ttk.Treeview(history_window, columns=("Timestamp", "Price"), show="headings")
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Price", text="Price ($)")
        tree.column("Timestamp", width=300)
        tree.column("Price", width=100, anchor="center")
        tree.pack(padx=20, pady=20, fill="both", expand=True)

        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        for _, price, timestamp in history:
            tree.insert("", "end", values=(timestamp, f"{price:.2f}"))

    def sort_column(self, col, reverse):
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children()]
        items.sort(reverse=reverse, key=lambda x: float(x[0]) if col in ["Target Price", "Latest Price"] and x[0] != "N/A" else x[0])
        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def check_prices_now(self):
        timestamp = check_prices()
        if timestamp:
            self.last_check_time = timestamp
            next_check = (datetime.now() + pd.Timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
            self.status_var.set(f"Last checked: {timestamp} | Next check: {next_check}")
        else:
            self.status_var.set("Check failed. See log for details.")

def main():
    init_db()
    root = tk.Tk()
    app = PriceTrackerApp(root)

    # Run schedule in background
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(60)

    import threading
    threading.Thread(target=run_schedule, daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    main()