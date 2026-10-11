# EE Agro-Chemicals 🌱

A simple stock and sales manager for an agro-chemicals shop, built with **Streamlit** and **Supabase**. Staff record sales at the counter, managers restock and reprice products, and the owner sees revenue at a glance.

## Features

- **🛒 Record Sales**: search products, see units available and price, enter the quantity sold and confirm. Stock updates instantly. Sold-out items are hidden from the counter.
- **📦 Inventory & Restock**: add a new shipment, update the price or delete a product. A warning banner lists items with fewer than 5 units left.
- **➕ Add New Product**: create a product with its starting quantity and price.
- **📈 Sales Report**: units sold, units in stock and revenue per product, plus total revenue.
- **Staff tracking**: each change stores the seller name entered in the sidebar (`updated_by`).
- **Low-stock email button**: intended to email the manager through EmailJS (see Known issues).

## Tech Stack

- [Streamlit](https://streamlit.io): UI
- [Supabase](https://supabase.com) (PostgreSQL): data storage
- [pandas](https://pandas.pydata.org): data handling
- [EmailJS](https://www.emailjs.com): low-stock email alerts

## Project Structure

```
.
├── app.py              # The whole app (your main Streamlit file)
├── requirements.txt
└── .streamlit/
    └── secrets.toml    # Keys (not committed)
```

## Setup

### 1. Install

```bash
pip install streamlit supabase pandas
```

`requirements.txt`:

```
streamlit
supabase
pandas
```

### 2. Create the Supabase table

Run this in the Supabase SQL editor:

```sql
create table inventory (
  item_name         text primary key,
  total_stock_input integer not null default 0,
  stock_remaining   integer not null default 0,
  price_per_unit    numeric not null default 0,
  updated_by        text,
  updated_at        timestamptz default now()
);
```

`item_name` must be unique because the app uses it for upserts.

### 3. Add your keys

Move the keys out of the code into `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://<project-ref>.supabase.co"
SUPABASE_KEY = "<publishable-key>"

EMAILJS_SERVICE_ID  = "service_xxxxx"
EMAILJS_TEMPLATE_ID = "template_xxxxx"
EMAILJS_PUBLIC_KEY  = "xxxxxxxx"
```

Then read them in `app.py`:

```python
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
```

On Streamlit Community Cloud, paste the same content into **Settings → Secrets**.

### 4. Run

```bash
streamlit run app.py
```

## How it works

| Action | What happens in the database |
|---|---|
| Confirm a sale | `stock_remaining` is reduced by the quantity sold |
| Restock | Quantity is added to both `total_stock_input` and `stock_remaining` |
| Add product | New row with `total_stock_input = stock_remaining = quantity` |
| Delete product | Row removed permanently |

Reports are calculated as:

- **Units sold** = `total_stock_input − stock_remaining`
- **Revenue** = units sold × current `price_per_unit`

## Known issues and improvements

- **No login or access control.** Anyone who opens the app can sell, reprice or delete products, and the seller name is just free text. Add authentication (for example Supabase Auth or `st.login`) and enable Row Level Security so only signed-in staff can write.
- **Low-stock email probably doesn't send.** Streamlit does not run `<script>` tags passed through `st.markdown`, and the button's HTML snippet runs in a separate frame where the EmailJS library isn't loaded. The reliable fix is to call the EmailJS REST API from Python:

  ```python
  import requests

  requests.post("https://api.emailjs.com/api/v1.0/email/send", json={
      "service_id": EMAILJS_SERVICE_ID,
      "template_id": EMAILJS_TEMPLATE_ID,
      "user_id": EMAILJS_PUBLIC_KEY,
      "template_params": {"message": msg, "to_name": "Manager"},
  }, timeout=10)
  ```

  If EmailJS rejects server-side calls, enable them in your EmailJS account settings.
- **The "stay awake" refresh tag likely does nothing.** The `<meta http-equiv="refresh">` inside `st.markdown` isn't applied. Free hosting sleeps after inactivity, so use an uptime pinger or a scheduled request to keep the app awake.
- **Revenue changes when prices change.** Revenue is computed from the current price, so editing a price rewrites past revenue. Add a `sales` table (item, quantity, price at sale, time, seller) for accurate history, daily totals and per-staff reports.
- **Deleting is permanent** and happens on one click. Add a confirmation step.
- **Overselling is possible** if two people sell the same item at once, because the app reads the stock, then writes the new total. Use a Supabase RPC or SQL function that decrements atomically.

## Security notes

- Keep keys in `secrets.toml`, not in the code, and add `.streamlit/secrets.toml` to `.gitignore`.
- A Supabase publishable key is meant to be public, but only when Row Level Security policies protect the table. Without them, anyone with the key can edit or delete your inventory.
- Restrict your EmailJS public key to your app's domain in the EmailJS dashboard.

## Author

**Okiror Innocent**, Computer Science student, Mbarara University of Science and Technology (MUST), Uganda.

## License

© 2026 EE Agro-Chemicals. All rights reserved.
