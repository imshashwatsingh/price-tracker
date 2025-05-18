# Price Tracker Bot

A Python-based web scraping tool that monitors product prices on Amazon, sends desktop notifications when prices drop below a user-defined threshold, and provides a modern GUI for managing tracked products. Built with `requests`, `beautifulsoup4`, `sqlite3`, `tkinter`, and `plyer`, this bot is ideal for personal use to track deals efficiently.

## Features

- **Web Scraping**: Extracts product names and prices from Amazon product pages with robust error handling and user-agent rotation.
- **Price Monitoring**: Tracks price history in a SQLite database and checks prices every 12 hours.
- **Desktop Notifications**: Alerts you via system notifications when a product's price drops below your target.
- **Modern GUI**: User-friendly interface with:
  - Add/remove products with URL and target price inputs.
  - Sortable table displaying product details (name, URL, target price, latest price).
  - Price history viewer for each product.
  - Status bar showing last and next check times.
  - Tooltips for long text and input guidance.
- **Error Handling**: Logs all actions and errors to `price_tracker.log` for debugging.
- **Customization**: Easily modifiable to support other websites or add features like price trend charts.

## Prerequisites

- **Python**: Version 3.6 or higher.
- **Dependencies**:
  - `requests`: For HTTP requests.
  - `beautifulsoup4`: For web scraping.
  - `schedule`: For scheduling price checks.
  - `pandas`: For data handling.
  - `plyer`: For desktop notifications.
- **Operating System**: Windows, macOS, or Linux (for `plyer` notifications).

## Installation

1. **Clone or Download**:
   - Download the `price_tracker.py` script or clone the repository.

2. **Install Dependencies**:
   ```bash
   pip install requests beautifulsoup4 schedule pandas plyer
   ```

3. **Verify Python**:
   Ensure Python is installed and accessible:
   ```bash
   python --version
   ```

## Usage

1. **Run the Script**:
   ```bash
   python price_tracker.py
   ```
   This launches the GUI at 09:45 PM IST, May 18, 2025, or anytime.

2. **Add a Product**:
   - Enter an Amazon product URL (e.g., a book or gadget page).
   - Specify a target price (e.g., `50.00` for $50).
   - Click **Add Product**. The product appears in the table.

3. **Monitor Prices**:
   - The bot checks prices every 12 hours automatically.
   - Click **Check Prices Now** for a manual check.
   - A desktop notification appears if a price drops below your target.

4. **Manage Products**:
   - **Remove Selected**: Select a product in the table and click to remove.
   - **Clear All**: Remove all tracked products (with confirmation).
   - **View Price History**: Select a product and click to see its price history in a new window.

5. **Check Logs**:
   - Open `price_tracker.log` for debugging if issues occur.

## GUI Overview

- **Header**: Clean teal header with the app title.
- **Input Fields**:
  - **Product URL**: Accepts Amazon URLs (validated).
  - **Target Price**: Numeric input for desired price.
- **Table**: Displays products with sortable columns (Name, URL, Target Price, Latest Price).
- **Buttons**:
  - **Add Product**: Adds a new product to track.
  - **Check Prices Now**: Triggers an immediate price check.
  - **Remove Selected**: Deletes the selected product.
  - **View Price History**: Shows price history for the selected product.
  - **Clear All**: Removes all products.
- **Status Bar**: Shows last check time and next scheduled check.

## Customization

- **Change Check Interval**:
  Modify `schedule.every(12).hours` in `PriceTrackerApp.__init__` to a different interval (e.g., `schedule.every(6).hours`).

- **Support Other Websites**:
  Update the `scrape_product` function's selectors to target other sites (e.g., eBay). For example:
  ```python
  price_elem = soup.select_one('.ebay-price-selector')  # Hypothetical eBay selector
  ```

- **Add Price Trend Charts**:
  Integrate `matplotlib` to plot price history. Add a button to trigger a graph in `view_price_history`.

- **Notification Timeout**:
  Adjust `timeout` in `send_notification` (default 10 seconds) for longer/shorter alerts.

- **UI Colors**:
  Change colors in the `style.configure` calls (e.g., `#26a69a` for teal) to match your preference.

## Troubleshooting

- **Scraping Fails**:
  - Check `price_tracker.log` for errors (e.g., "Failed to scrape").
  - Ensure the URL is a valid Amazon product page.
  - Amazon may block requests; increase the check interval or add proxies.

- **No Notifications**:
  - Verify `plyer` is installed (`pip install plyer`).
  - Ensure the script is running when a price check occurs.
  - Check if the price is below the target and no prior notification was sent (stored in `last_notified_price`).

- **GUI Issues**:
  - Ensure `tkinter` is available (usually included with Python).
  - If the table doesn't display, check `price_tracker.db` for data corruption.

- **Database Errors**:
  - Delete `price_tracker.db` and restart the script to recreate it.
  - Ensure write permissions in the script's directory.

## Limitations

- Designed for Amazon; other sites require selector modifications.
- Frequent scraping may trigger Amazon's anti-bot measures.
- Desktop notifications require the script to be running.
- Price history viewer is table-based; graphs require additional code.

## Contributing

Feel free to fork the project, add features (e.g., multi-site support, price graphs), and submit pull requests. Report issues via the repository's issue tracker.

## License

MIT License. See `LICENSE` file for details (if included).

## Acknowledgments

- Built with Python, `tkinter`, and open-source libraries.
- Inspired by personal needs for deal tracking on Amazon.

---

*Last updated: May 18, 2025, 09:45 PM IST*